# T-CLD-03-E — Expert Depth

*Chapter: [T-CLD-03 — Cloud Foundations and Governance](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-03-e"></a>
#### T-CLD-03-E — Expert Depth

## Why this level exists

By Professional level you can design a governed organisation: layered policy, separated duties, allocated cost, evidenced controls. Expert practice begins where that design meets time, scale and disagreement. The organisation acquires another company with its own accounts and its own provider. A business unit has a risk profile utterly unlike the rest. A regulator changes a rule. A critical team needs an exception that the control owner does not want to give. A foundation built three years ago in a hurry now carries two hundred workloads and nobody dares touch it.

The Expert question is therefore not "which control should exist?" but "**how does a foundation evolve without breaking the people standing on it, and how do I decide, with numbers and with honesty about uncertainty, where to spend limited governance effort?**" This section covers landing zones as long-lived products across multiple organisations, differentiated governance for different risk profiles, the economics of reliability versus cost, exceptions as a designed system, regulatory change, and the migration of weak foundations to strong ones.

It assumes the previous levels. Policy snippets, numbers and scenarios are **illustrative**; use them to build your own calculations, not to copy figures. Regulatory examples are generic and are not legal advice.

## First principles: a landing zone is a product, and governance is a market

Two ideas organise everything below.

**A landing zone is a product.** It has users (engineering teams), an interface (account vending, baseline templates, documentation), guardrails, a support model, a roadmap and — crucially — *competitors*: the unofficial paths teams take when the product is slow or restrictive. Account creation should be self-service with baseline configuration applied automatically: logging, identity federation, network attachment, budgets, security tooling. Break-glass access is separately controlled, monitored and tested.

**Governance is a market with friction.** Every control imposes friction on someone. People respond to friction by complying, requesting exceptions, or bypassing. A governance system that ignores the bypass option accumulates shadow accounts, ungoverned spend and screenshots. A system that makes the compliant path the *cheapest* path wins by economics rather than by enforcement.

| Product thinking | Governance consequence |
| --- | --- |
| Users have alternatives | Measure adoption, not just compliance |
| Interfaces need versioning | Baseline changes must roll out safely and predictably |
| Support is part of the product | Time to answer "why was I denied?" is a feature |
| Roadmaps need priorities | Spend effort where loss prevented per unit friction is highest |
| Deprecation is hard | Old baselines must be migrated, not abandoned |

## Preventive, detective, corrective: choosing the mix

Preventive controls (denying public storage at the organisation level) are strongest but can block legitimate work and need an exception process. Detective controls find drift but depend on response. Corrective automation (auto-remediation) is powerful and risky — it can cause outages; scope and test it. Design the exception path first, with owners and expiry.

A decision frame for which type to use:

| Question | If yes | If no |
| --- | --- | --- |
| Is the harm severe or irreversible (data exposure, evidence loss)? | Prefer preventive | Detective may suffice |
| Is there rarely a legitimate reason for the action? | Preventive is cheap | Detective plus review |
| Can the rule be expressed precisely in policy conditions? | Preventive is feasible | Detective with human judgement |
| Is response time short and the remediation safe? | Corrective is viable | Alert and ticket |
| Is the population of accounts mature and tested? | Stricter controls | Start detective, tighten after data |

### Choosing the first three guardrails: a defensible method

Do not start from a list of every best practice; start from the loss each guardrail prevents, the cost of false positives and whether the control can be bypassed.

| Candidate guardrail | Prevents | Cost if wrong | Good first-wave? |
| --- | --- | --- | --- |
| Deny disabling audit logging and deleting log archives | Loss of evidence after a compromise | Almost none; legitimate work does not need it | Yes |
| Restrict permitted regions | Shadow resources in unused regions; data-residency breaches | Occasional blocked experiment | Yes, with an exception path |
| Deny leaving the organisation and deleting the account's baseline roles | Accounts escaping governance | Almost none | Yes |
| Deny public object storage (account-level block) | Data exposure | Breaks legitimate public websites | Yes, with a documented exception route for approved public buckets |
| Require a specific instance family | Cost consistency | High friction, little risk reduction | No |

Order by (risk prevented) ÷ (friction caused) and by how cheaply you can prove the control works. Each guardrail should have a test that tries the forbidden action in a sandbox account and expects a deny; that test is the evidence.

## Multi-organisation landing-zone evolution

Single-organisation designs are the textbook case. Real enterprises end up with **several organisations** (or the equivalent): through acquisition, through separate legal entities, through regulatory ring-fencing of a business line, through a deliberate split between production and "everything else", or through history. Plan for it.

### Why organisations multiply

| Cause | Typical shape | Governance challenge |
| --- | --- | --- |
| Acquisition | A second organisation with its own identity provider and tooling | Merge, federate or keep separate? |
| Legal separation | A subsidiary that must not share administrative control with the parent | Independent management planes |
| Regulatory ring-fence | A regulated business needs stricter, isolated governance | Different control sets, evidence regimes |
| Multi-cloud | Another provider for a specific capability | Different primitives; common intent |
| Isolation of the crown jewels | A separate organisation for the log archive or key custody | Independence from compromise of the main one |
| Customer-dedicated environments | A tenant's workload in its own organisation | Scale of vending and cost visibility |

### The evolution stages

A landing zone typically moves through recognisable stages. Knowing the stage tells you what to build next and what *not* to build yet.

```text
Stage 0  Ad hoc        One or few accounts; manual setup; shared admin.
Stage 1  Baseline      Org created; SSO; org trail; first-wave guardrails; manual vending.
Stage 2  Automated     Account vending as code; baseline stacks; register; automated evidence.
Stage 3  Differentiated  OU-specific control sets for risk profiles; exception system; unit cost.
Stage 4  Federated     Multiple organisations/clouds under one governance model; common control
                         catalogue with provider-specific implementations; central evidence.
Stage 5  Adaptive      Controls measured for cost and effect; automated retirement of obsolete
                         controls; regulatory changes absorbed through the catalogue.
```

Moving a stage costs effort; skipping ahead produces ceremony without substance (for instance, a federated governance model for twelve accounts).

### Federating several organisations

Three patterns, in increasing coupling:

| Pattern | Description | Strength | Weakness |
| --- | --- | --- | --- |
| Independent | Each organisation self-governs, with a shared standard document | No cross-dependency | Drift; hard to prove consistency |
| Common catalogue | One control catalogue; each organisation implements it with its own tooling; evidence is collected centrally | Consistency of intent; local autonomy | Evidence mapping effort |
| Shared management plane | Central platform manages all organisations | Strongest consistency | A single point of compromise across all organisations |

The risk to name in the third pattern is **concentration**: a central pipeline holding administrative roles in every organisation is the most valuable target you have. Protect it as a crown jewel: separate organisation, hardware-backed authentication, no human interactive access, mandatory two-person change, extensive logging held outside its own control.

A useful structure is the **independent evidence plane**: whichever pattern you choose, collect evidence into a separate organisation that the others write to but cannot modify.

```text
Org A (prod)  ----\
Org B (acquired) ---+--> Evidence organisation (write-only ingestion, object lock, read by audit only)
Org C (regulated) -/
```

### Identity across organisations

| Option | Description | Trade-off |
| --- | --- | --- |
| One identity provider, federated to all | Single directory and MFA policy | Strong consistency; the provider is a concentration point |
| Per-organisation identity, synchronised groups | Local resilience; mapping effort | Group drift |
| Per-organisation identity, no synchronisation | Total independence | Joiner/leaver processes multiply; leavers missed |

Joiners, movers and leavers are the main risk: measure the time from HR leaver event to last active session revoked in *each* organisation; the slowest governs your exposure.

### Network and naming across organisations

Pre-allocate address space from one registry across all organisations, even if they never connect today: acquisitions that later need connectivity are blocked by overlapping ranges more than by any other single technical issue. Keep one naming convention and one tag schema. Mapping tags between organisations later is possible but expensive.

### Evolution without breaking users: baseline versioning

Baseline changes (a new guardrail, a new logging configuration) must reach hundreds of accounts without surprises. Treat the baseline as a versioned release.

```text
baseline v1.4  adds: deny creation of long-lived access keys for human users
Rollout plan
  Week 0   Announce; publish diff and test; list affected accounts from inventory query
  Week 1   Detective mode in all accounts (findings only)
  Week 2   Enforce in sandbox and nonprod canary OUs
  Week 4   Enforce in remaining nonprod; exceptions recorded with expiry
  Week 6   Enforce in prod OU; remaining exceptions reviewed
  Rollback Detach policy by pipeline job (documented); decision owner: platform lead
Success   0 legitimate denials for 7 days; findings burn down to documented exceptions only
```

Keep at most two baseline versions live; track adoption per version; define the date when the old version stops being supported.

## Varied risk profiles: differentiated governance

A single governance level for everything is wrong in both directions: too loose for the payment system, too tight for a student sandbox. Differentiation is a feature of mature landing zones, but it must be *simple enough to explain*.

### Risk profiles as tiers

Define a small number of tiers (three or four) with explicit criteria, and attach controls to tiers rather than to individual accounts.

| Tier | Typical workload | Data class | Control posture |
| --- | --- | --- | --- |
| T0 Sandbox | Learning, experiments | None or synthetic | Budget cap, auto-cleanup, no connectivity to other tiers |
| T1 Internal | Internal tools, non-sensitive services | Internal | Standard baseline; detective-first; self-service |
| T2 Business-critical | Customer-facing production | Confidential | Strict preventive guardrails; reviewed pipeline; evidence continuous |
| T3 Regulated / crown jewels | Payments, health data, key custody, log archive | Restricted | Allow-list services; customer-managed keys; two-person changes; dedicated evidence regime |

### What changes by tier

| Dimension | T0 | T1 | T2 | T3 |
| --- | --- | --- | --- | --- |
| Account vending time | Minutes | Hours | Days (review) | Days to weeks (review plus risk sign-off) |
| Human write access | Broad | Team | Pipeline plus break-glass | Pipeline only; two-person approvals |
| Region and service scope | Few regions, wide services | Approved regions | Approved regions, reviewed services | Allow-list of services and regions |
| Network | Isolated | Shared hub | Controlled egress | Private-only; egress inspection |
| Logging | Org trail | Org trail plus flow logs (selected) | Plus data events for sensitive stores | Full, immutable, longer retention |
| Exceptions | Auto-approved within limits | Owner approval | Owner plus security | Architecture board |
| Evidence cadence | Quarterly | Monthly | Continuous | Continuous plus independent review |

### Rules for tiering that keep it honest

- **Tier by data and impact, not by team prestige.** A small team can run T3 data.
- **No connectivity from low to high tier by default.** A T0 sandbox that can reach a T3 database makes the T3 label false.
- **Promotion is a process.** Moving a workload up a tier requires meeting the higher baseline, with a checklist; demotion needs data deletion or reclassification evidence.
- **Few tiers.** Each added tier multiplies catalogue entries, evidence, and training.
- **Mixed-tier workloads are named for the highest tier of data they touch.** A data pipeline that collects restricted data is T3 regardless of its purpose.

### Illustrative guardrail by tier

```text
SCP-017 (T3 OUs only): allow-list of services
   Allowed services: compute, container, relational DB, object storage, KMS, logging, monitoring
   Everything else: implicit deny; new service requires architecture board review
SCP-018 (T2 and T3): deny creation of internet gateways outside the shared edge account
SCP-019 (T0): deny instance types above a size ceiling; deny creation of VPC peering to non-T0
```

### Tension: different risk profiles in one platform

When one organisation hosts all tiers, **shared dependencies** couple them. The platform team's CI runner, container registry, DNS zone, logging pipeline or network hub is a path from T1 to T3. List shared dependencies and ask for each: *if this is compromised, which tier is reachable?* Either the dependency is hardened to the highest tier it serves, or it is split per tier.

## Cost versus reliability

Cost behaves like latency: it appears from design decisions and compounds. Reliability is bought; the question is how much to buy.

### Cost as an architectural property

Include cost in design reviews, set unit-cost targets (cost per request or per customer), and treat unexplained cost changes as incidents. Weigh commitment discounts against flexibility and consider exit costs (data egress, proprietary service coupling) when assessing lock-in.

### Resilience at the provider level

Understand blast-radius boundaries: availability zone, region, account, provider. Decide per workload the failure you design for and the one you accept; test it. Multi-region is expensive and complex — justify with business impact analysis (recovery time and recovery point objectives), not fashion. Beware hidden shared dependencies (global control planes, identity services, DNS).

### The reliability ladder

| Level | Design | Typical cost multiple of single-instance baseline (illustrative) | Survives |
| --- | --- | --- | --- |
| 0 | Single instance, single zone | 1.0 | Nothing in particular |
| 1 | Backups to another zone/region | 1.1 | Data loss from deletion or zone loss (slow recovery) |
| 2 | Multi-AZ active-active with spare capacity | 1.5–2.0 | Zone failure with little or no interruption |
| 3 | Warm standby in another region | 2.0–3.0 | Regional failure with minutes to hours of recovery |
| 4 | Active-active multi-region | 3.0–5.0 | Regional failure with little interruption |
| 5 | Multi-provider | 4.0+ | Provider-level failure; heavy engineering burden |

Each rung has a cost in **operational complexity** as well as money. A multi-region design that nobody has failed over has a probability of working that is lower than people assume.

### Multi-region as a decision, with numbers

Suppose `orders-api` earns about 2,000 per hour and is down for a regional outage once every five years for about four hours. Expected loss is roughly 8,000 per five years, or 1,600 per year. A warm standby costing 60,000 per year is not justified by that alone; a regulatory requirement or reputational impact might justify it, and backup-and-restore in another region (cheaper, with an RTO of hours) may cover most of the risk. Include hidden shared dependencies in the analysis: if identity, DNS or the deployment pipeline sits in the failed region, the "standby" cannot be operated. Then test the failover yearly, otherwise the cost buys only a belief.

A reusable structure for the calculation:

```text
Annual expected loss = sum over failure modes of ( frequency per year x duration in hours x loss per hour )
Residual after design = same sum with the design's recovery time and data-loss window applied
Benefit of design    = Annual expected loss  -  Residual after design
Net                  = Benefit  -  Annual cost of design (infrastructure + people + testing)
Add separately: non-financial impact (regulation, safety, reputation, contract penalties)
```

Worked comparison (all figures illustrative):

| Option | Annual cost | Zone-loss residual | Region-loss residual | Net benefit versus single-AZ |
| --- | --- | --- | --- | --- |
| Single AZ | 0 | one zone event per 3 years x ~3 h x 2,000 = 2,000 per year | 1,600 per year | baseline |
| Multi-AZ | 12,000 | ~100 per year | 1,600 per year | +1,900 + 0 − 12,000 = −10,100 on money alone |
| Multi-AZ + cross-region backups | 15,000 | ~100 | ~800 (RTO about 4 h cut to ~2 h) | negative on money; may be required by data-loss rules |
| Warm standby | 60,000 | ~100 | ~200 | negative unless impact includes penalties or regulation |

Money-only analysis often says "do less" for small services. That is exactly why the *non-financial* column matters, and why you should write down the assumptions (failure frequency, loss per hour) so they can be challenged and revised.

Also consider **correlated failure**: if two "independent" designs share a control plane, a certificate expiry or a bad deployment, they fail together. Resilience that depends on independence you have not verified is aspirational.

### Unit cost and exit cost

| Metric | How to compute | Use |
| --- | --- | --- |
| Unit cost | Monthly attributable cost ÷ business unit (orders, active customers) | Spot design regressions; compare architectures |
| Commitment coverage | Share of steady-state usage under commitment discounts | Avoid paying on-demand for predictable load, or over-committing |
| Exit cost | Data egress + re-engineering of proprietary services + team learning | Informs lock-in decisions; compare against the benefit of managed services |

Lock-in is not automatically bad. Ask what the proprietary service gives you, what leaving would cost today, and whether a portability layer (open protocols, standard databases, containers) is cheaper than the risk it reduces. Record the answer so it can be revisited.

### Cost reliability trade-offs that bite

| Design choice | Cost effect | Reliability effect | Gotcha |
| --- | --- | --- | --- |
| Spare capacity in each zone | Higher steady cost | Zone loss survivable | Utilisation target must reflect N−1 capacity |
| Cross-zone traffic | Per-gigabyte charge | Required for multi-AZ replication | Chatty services produce large transfer bills |
| Interruptible (spot-like) instances | Large discount | Capacity can vanish | Only for fault-tolerant, stateless work |
| Long log retention | Storage cost | Better forensics | Tiering and sampling reduce cost |
| Over-aggressive rightsizing | Lower cost | Less headroom | A rightsized system fails at the first spike |
| Commitment discounts | Lower unit price | None directly | Locks you to an instance family or region |

## Exceptions as a designed system

Exceptions are not failures of governance; they are the pressure-release valve that keeps governance from being bypassed. Designing the exception path is part of the control.

### The exception path

```text
Request:   control ID, account, resource, reason, requested duration (max 90 days)
Approval:  control owner + account owner; security approves anything touching data
Mechanism: time-boxed policy attachment or tag-based condition; auto-removed at expiry
Record:    stored in the register with owner, compensating control, expiry
Review:    list of active exceptions reviewed monthly; renewals need fresh justification
```

Measure the path: median time to decision, number of active exceptions, exceptions past expiry (target zero) and the share that became permanent changes to the guardrail itself (a signal that the control is wrong).

### Exception taxonomy

| Type | Example | Handling |
| --- | --- | --- |
| Temporary technical | A migration needs public access for two weeks | Time-boxed; compensating control; auto-expiry |
| Permanent legitimate | A public marketing website bucket | Convert to a documented pattern or a scoped carve-out in the policy |
| Capability gap | The control cannot support a needed service yet | Risk acceptance with an owner and a remediation roadmap |
| Business override | An executive demands access to a restricted area | Formal risk acceptance signed at the appropriate level; logged |
| Emergency | Production incident needs a control lifted | Break-glass; post-incident review within 24 hours |

### Implementing an exception safely

A tag-based exception avoids editing the policy for each request:

```json
{
  "Sid": "DenyPublicBucketsUnlessApproved",
  "Effect": "Deny",
  "Action": ["s3:PutBucketPublicAccessBlock", "s3:DeletePublicAccessBlock"],
  "Resource": "*",
  "Condition": {
    "StringNotEquals": { "aws:ResourceTag/PublicAccessException": "approved" }
  }
}
```

Combine it with a rule that only the exception-approval automation may set that tag, with the tag carrying an expiry value that a scheduled job checks:

```text
Daily job:
  for each resource tagged PublicAccessException=approved:
      if ExceptionExpiry < today: remove tag, alert owner, open ticket
      if no matching record in the exception register: remove tag, alert security
```

### Exception metrics and what they reveal

| Metric | Healthy | Signal when unhealthy |
| --- | --- | --- |
| Median time to decision | Hours to a day for routine | Teams bypass the process |
| Active exceptions per control | Few, mostly temporary | The control is wrong or the pattern is missing |
| Exceptions past expiry | Zero | Weak ownership; automation gaps |
| Renewal rate | Low | A permanent need hidden as a temporary one |
| Denied-without-appeal count | Low | Friction unaddressed |

When the renewal rate on one control rises, change the control. An exception that is renewed five times is a policy defect, not a special case.

## Regulatory landscapes

Regulation arrives from outside, changes on its own timetable and varies by jurisdiction and sector. The architecture must absorb change without a rebuild.

### Model regulation as requirements on controls

Do not treat each regulation as a separate project. Maintain a **requirements register** mapped to the control catalogue:

```text
Requirement    R-REG-211  Personal data of residents must be stored in the approved legal area.
Source         Regulation X, article n (generic example)
Applies to     T2 and T3 workloads handling personal data
Controls       SCP-007 (regions), SCP-011 (replication), KMS-004 (key location), EV-031 (inventory evidence)
Owner          Data protection officer (policy) / platform lead (implementation)
Evidence       Nightly inventory by region; quarterly access review of support grants
Gaps           Provider support access (contractual); review due 2027-01
```

### Typical regulatory themes and their foundation implications

| Theme | Foundation implication |
| --- | --- |
| Data residency and transfer limits | Region controls, replication limits, key location, support-access terms |
| Operational resilience (financial or critical sectors) | Documented impact tolerances, tested failover, exit plans from providers |
| Third-party / outsourcing risk | Provider due diligence, contract clauses, concentration-risk assessment, audit rights |
| Security frameworks (control catalogues) | Mapped controls; continuous evidence; independent assessment |
| Privacy | Data classification, retention, deletion, access logging, breach notification process |
| Sector-specific rules (payments, health) | Tier-3 baseline: allow-listed services, segmentation, dedicated evidence regime |
| Records retention | Immutable storage; retention schedules; legal-hold capability |

### Exit plans and concentration

Operational-resilience rules increasingly require **exit plans**: a described, tested way to leave a provider or to continue operating if it fails. At the foundation level that means:

- Inventory of provider-specific services per critical workload and an assessment of substitutes.
- Data export procedures tested at realistic scale, with egress cost estimated.
- Infrastructure defined as code so that rebuild elsewhere is feasible, noting where provider-specific resources dominate.
- A realistic statement of what *cannot* be replaced and the compensating risk acceptance.
- A stressed-exit scenario: partial exit of a single workload is more testable than a full exit.

### Absorbing a regulatory change

```text
1. Read the change; extract requirements; identify the tiers and workloads in scope.
2. Map to existing controls; identify gaps (controls missing, evidence missing).
3. Estimate effort and deadline; decide implement, accept risk, or exit scope.
4. Implement through the catalogue and baseline versioning (canary, rollout, evidence).
5. Update the requirements register and evidence; brief the control owners.
6. Verify with an internal review before an external one.
```

The speed with which you can answer "which accounts does this affect, and what is our current evidence?" is a direct measure of governance maturity.

## Migrating weak foundations

Most organisations do not start greenfield. They have accounts created ad hoc, shared admin users, no central logs, inconsistent tags and a cloud bill that is a mystery. Migration is a change programme, not a technical exercise.

### Diagnose first: the foundation health check

```text
Identity      Count of human IAM users; long-lived access keys older than 90 days; MFA gaps.
Structure     Accounts outside the organisation; workloads in the management account.
Logging       Accounts without audit logging; logs in the same account; retention gaps.
Network       Public exposures; overlapping address ranges; unmanaged peering.
Data          Public storage; unencrypted volumes and databases; backup coverage.
Cost          Untagged spend share; idle resources; commitment coverage; anomalies.
Exceptions    Undocumented deviations; permanent "temporary" access.
```

Quantify each: counts and percentages. A migration plan without baseline measurements cannot show progress.

### Sequencing: stop the bleeding, then build the new

| Phase | Goal | Typical actions | Risk |
| --- | --- | --- | --- |
| 0 Stabilise | Stop growth of the problem | Freeze new unmanaged accounts; require MFA; enable organisation trail; alert on root use | Low |
| 1 Visibility | See everything | Inventory accounts, identities, resources and cost; tag baseline; centralise logs | Low |
| 2 Contain | Reduce worst exposure | Remove public data; rotate old keys; disable unused users; deny leaving organisation | Medium: may break hidden dependencies |
| 3 Structure | Introduce the new layout | Create new OUs and baseline; vend new accounts; start moving workloads | Medium |
| 4 Migrate | Move workloads into governed accounts | Per-workload plans; dual-run where needed | High: requires owners' time |
| 5 Retire | Close old accounts and legacy identities | Verified decommissioning | Medium |
| 6 Sustain | Keep it from decaying | Evidence pipelines; reviews; metrics | Low |

### The hard parts

**Hidden dependencies.** Old accounts have roles, trust policies, bucket policies and DNS entries that nobody remembers. Before denying or deleting, *observe*: audit-log queries for the last 90 days of activity by role, key and trust relationship.

```sql
-- Which access keys are still used? (illustrative)
SELECT useridentity.accesskeyid, useridentity.username, max(eventtime) AS last_use, count(*) AS calls
FROM audit_logs
WHERE eventtime > now() - interval '90' day
  AND useridentity.accesskeyid IS NOT NULL
GROUP BY 1, 2
ORDER BY last_use ASC;
```

Keys with no use in 90 days are candidates for deactivation (not deletion): deactivate, wait, then delete when no one has complained for a defined period.

**Moving an account into the organisation.** Joining an existing account to an organisation may bring policies and billing consolidation immediately; check that guardrails will not break running workloads, and apply them first at an OU that is detective-only.

**Moving workloads versus moving accounts.** Sometimes it is easier to re-create the workload in a vended account (with infrastructure as code) than to refactor the old one. Decide per workload using a simple scoring:

| Factor | Re-platform into a new account | Adopt existing account in place |
| --- | --- | --- |
| Infrastructure defined as code | Yes → easy to recreate | No → recreating is a rewrite |
| Stateful data | Small → migrate | Large → egress and cutover risk |
| Dependencies on account-specific identifiers | Few | Many (hard-coded ARNs, allow-lists) |
| Team capacity | Available | Constrained |
| Risk level | High → clean start is safer | Low → minimal change |

**Cultural resistance.** Teams that managed their own accounts experience governance as loss of control. Offer something: faster vending, centralised logging they no longer need to run, cost visibility, reduced audit effort. Measure and share the time saved.

### A migration timeline with checkpoints (illustrative)

```text
Month 0-1   Stabilise: MFA gaps closed, org trail on everywhere, root alerts, freeze on unmanaged accounts.
Month 1-3   Visibility: inventory, tagging baseline, cost dashboards, health-check scores published.
Month 3-6   Contain + structure: remove public data, rotate keys, deploy OUs, baseline v1, vend first accounts.
Month 6-12  Migrate workloads by tier: T3 and T2 first (risk), then T1; sandboxes last.
Month 12-15 Retire legacy accounts; evidence pipelines in place; first internal audit.
Checkpoints Each month: health-check metrics; number of workloads migrated; exceptions; incidents.
Exit        Unmanaged accounts 0; keys > 90 days 0; untagged spend < 2 %; evidence coverage 100 %.
```

### Metrics for a migration

| Metric | Start | Target | Why |
| --- | --- | --- | --- |
| Human long-lived access keys | 63 | 0 | Credential theft surface |
| Accounts outside the organisation | 9 | 0 | Governance reach |
| Accounts with audit logging to the archive | 40 % | 100 % | Evidence |
| Untagged spend | 38 % | < 2 % | Attribution |
| Public storage buckets without exception | 17 | 0 | Exposure |
| Workloads in governed accounts | 20 % | 100 % | Coverage |

## Failure modes of governance, with measurable defences

| Failure | Mechanism | Measure that it is happening | Defence with a number |
| --- | --- | --- | --- |
| Policy sprawl | Many overlapping rules nobody understands | Number of policies per account; time to explain why a request was denied | Fewer, composable controls; every control has an owner, test and review date; any deny explained in under 15 minutes |
| Shadow accounts | Teams create their own to avoid friction | Accounts outside the organisation found via billing or SSO audits | Deny leaving the organisation; quarterly reconciliation of billing contacts; zero unmanaged accounts |
| Break-glass abuse | Emergency access becomes routine | Break-glass logins per quarter | Alert on every use; rotation after use; review within 24 hours; use only for declared incidents |
| Orphaned resources | No ownership or expiry | Resources without `owner` and `expires` tags | Mandatory tags, daily report, auto-stop of non-production after expiry; under 2 % untagged spend |
| Compliance by screenshot | Manual evidence | Evidence older than its control's check period | Automated checks that produce time-stamped results |
| Concentration risk | One account or region holds everything | Single points: one log bucket, one pipeline role, one key | Backup accounts, cross-region copies of critical data, separate custody of keys |
| Control rot | Policies outlive the risk they addressed | Controls with no denials and no review for a year | Annual review; retire or justify |
| Alert fatigue | Too many low-value findings | Findings acknowledged without action | Tune; severity thresholds; target actionability rate above 70 % |
| Over-privileged automation | Pipeline role is administrator everywhere | Policies with wildcard actions on pipeline roles | Scope per account and per stack; permission boundaries |

## Account-per-environment versus account-per-team: a comparison

| Dimension | Account per environment (dev, staging, prod) | Account per team (and environment) |
| --- | --- | --- |
| Blast radius | Large within an environment: any team can affect another's resources in prod | Small: team boundaries match account boundaries |
| Cost attribution | Needs strict tagging to attribute spend to teams | Natural: the account's bill belongs to the team |
| Operational overhead | Low: few accounts | High without automation: many baselines to maintain |
| Access control | Complex permission conditions within shared accounts | Simpler: grant per account |
| Shared service reach | Easy | Needs cross-account patterns (networking, DNS, identity) |
| Best fit | Small organisations, few teams | Larger organisations with mature account vending |

A common middle path is a workload account per team per environment (or per product) for production and shared accounts for non-production experiments, because the compounding factor is how cheaply you can vend and baseline an account. If creating an account takes two weeks and a ticket, teams will share accounts regardless of what the standard says.

## Evidence that the landing zone is used

Share of workloads running in vended accounts; share of new accounts created by the vending path rather than by hand; median time to a baselined account; number of exceptions and their ages; teams that built their own parallel baseline (a sign the product failed on friction).

| Adoption metric | Healthy reading | Warning reading |
| --- | --- | --- |
| Workloads in vended accounts | Above 95 % of production | Large legacy remainder with no plan |
| Accounts created outside vending | Zero | Any: investigate cause |
| Median vending time (T1) | Under a day | Several days: shadow accounts likely |
| Baseline drift | Under 2 % of accounts with drift | Rising; automation not enforcing |
| Exception age | Median under 45 days | Many beyond 90 days |
| Team satisfaction (short survey) | Improving | Declining despite compliance: friction too high |

## Case catalogue

**Case 1: the acquired company.** A firm acquires a startup whose twenty accounts have shared admin keys and no logs. The first week: join the accounts to a *detective-only* OU, enable the organisation trail, alert on root, and snapshot an inventory. Governance did not break the startup's deployments because nothing was denied until usage queries showed which roles and keys mattered. Lesson: observe, then constrain.

**Case 2: the region deny that broke a website.** A region-deny policy was rolled out to production without checking global services. Certificate and edge-service operations that route through a global service's home region failed. The fix was a short exemption list for global services and a canary stage in the process. Lesson: policies have implicit dependencies; test them against real activity.

**Case 3: the log archive in the wrong account.** Logs lived in the same account as the workload. After a compromise, the attacker deleted the trail and the bucket. The organisation had no evidence of the first week. Lesson: evidence must live where the audited party cannot reach.

**Case 4: the exception that became the platform.** A "temporary" exception for public storage was renewed eleven times; eventually seven teams used it. The control was redesigned: approved public buckets are created via a module that enforces content restrictions, with a narrow policy carve-out. Lesson: a renewed exception is a missing pattern.

**Case 5: the multi-region that could not fail over.** A warm standby existed in another region, but the CI/CD system and the identity provider's admin plane lived only in the primary. During a regional outage the standby was running and unreachable for deployment changes and administrator sign-in. Lesson: dependency graph analysis, then a failover test that includes the *operators'* tooling.

**Case 6: the unit-cost regression.** After a release, cost per order rose 40 % without traffic change. Investigation: debug-level logging enabled in production plus a new cross-zone chatty call. The unit-cost alert caught it in three days. Lesson: cost anomalies are incidents with unit-cost context.

**Case 7: the central pipeline as a single point of failure.** A shared deployment role with administrator rights across all accounts was assumed by a compromised build agent. Containment required revoking sessions in forty accounts. Lesson: scope pipelines per account or tier, with permission boundaries; concentrate monitoring where concentration exists.

## Expert trade-offs

| Decision | Option A | Option B | What decides it |
| --- | --- | --- | --- |
| Governance strictness | Strong preventive denies, few exceptions | Detective-first with fast response | Severity and reversibility of harm; maturity of detection |
| Platform ownership | Central platform team owns baseline | Federated teams own baselines within a standard | Scale; skill distribution; regulatory need for uniformity |
| Federation | Common catalogue, local tooling | Shared management plane | Concentration risk tolerance; speed of change |
| Resilience spend | Multi-AZ plus tested backups | Warm standby or active-active | RTO/RPO from business impact; regulation; verified independence |
| Tiering | Few tiers | Many tiers | Ability to explain and evidence each tier |
| Lock-in | Managed proprietary services | Portable layer | Exit cost versus operating burden; regulatory exit plan |
| Migration style | In-place adoption | Re-platform into vended accounts | IaC maturity; data size; ownership |
| Cost controls | Hard limits (quotas, denies) | Alerts and showback | Culture; harm of overspend versus harm of blocking |

## Knowledge consolidation

- A **landing zone is a product** in competition with unofficial paths; its adoption, friction and support are governance properties. Governance is a market with friction.
- Choose **preventive, detective or corrective** by severity, reversibility, precision and the maturity of response. Begin with a few guardrails ranked by risk prevented per unit friction, each with a test.
- Multi-organisation estates need **common intent and independent evidence**; shared management planes concentrate risk and must be protected as crown jewels.
- **Baseline versioning** with canary rollout, detective mode, expiry of exceptions and a named rollback lets the foundation evolve without breaking users.
- **Tier workloads** by data and impact; few tiers, no default low-to-high connectivity, explicit promotion, and attention to **shared dependencies**.
- **Cost versus reliability** is an expected-loss calculation with stated assumptions and non-financial factors; multi-region value depends on **tested** failover and verified independence of dependencies.
- **Exceptions** are a designed, measured system with expiry; a repeatedly renewed exception reveals a defective control or missing pattern.
- **Regulation** is modelled as requirements mapped to controls and evidence, so change is absorbed through the catalogue; exit plans and concentration risk are foundation concerns.
- **Migrating weak foundations** follows stabilise, observe, contain, structure, migrate, retire, sustain; observe usage before denying or deleting; measure progress with numbers.
- Evidence that governance works is **adoption plus outcomes**, not the existence of documents.

## Exercises

**Exercise 1 — Guardrail ranking.** List ten candidate guardrails for a newly formed organisation. For each, estimate harm prevented, friction caused, ability to test and bypass difficulty. Rank by risk prevented per unit friction, choose the first three and write the sandbox test for each.

**Exercise 2 — Multi-organisation design.** A company will acquire two firms in different legal entities, one on a different cloud provider. Choose between independent, common-catalogue and shared-management-plane patterns. Draw the identity, evidence and network arrangements, name the main concentration risk and state what would make you change the choice.

**Exercise 3 — Tier design.** Define three risk tiers with entry criteria. For a payments service, a marketing website and a data-science sandbox, assign tiers and explain what shared dependencies could breach tier separation.

**Exercise 4 — Reliability economics.** A service earns 5,000 per hour; zone failures occur about once a year for two hours (with a single-AZ design) and regional failures once in ten years for six hours. Compute expected annual loss for single-AZ, multi-AZ (zone residual 10 %) and warm-standby (region residual 5 % of baseline). Add costs of 0, 18,000 and 90,000 per year, discuss the result, and list three non-financial factors that could change the decision.

**Exercise 5 — Exception system.** Design an exception process for public storage. Include request data, approvals, mechanism, expiry automation, metrics, and a rule for converting recurring exceptions into patterns.

**Exercise 6 — Regulatory change.** A new rule requires that personal data of residents never leave an approved legal area and that providers have tested exit plans. Write the requirements register entries, map them to controls and evidence, identify gaps and propose a six-month plan.

**Exercise 7 — Migration plan.** An organisation has 55 accounts, 40 of them outside the organisation, 120 human access keys, 30 % of accounts with audit logging and 45 % untagged spend. Produce a phased plan with a first-month action list, baseline metrics, targets, and how you will discover hidden dependencies before enforcement.

**Exercise 8 — Failure drill.** Run a tabletop for these events in order: a shared pipeline role is compromised; the compromise spreads to two accounts; an engineer asks for a temporary exception to the quarantine policy to fix a customer issue. Decide who decides what, what you cut, and how you record and later review the exception.

**Exercise 9 — Adoption diagnosis.** Vending takes six working days, 30 % of new accounts bypass it and the exception renewal rate is 60 %. Diagnose the likely causes, choose three actions with measurable targets, and say how you would know each worked after a quarter.

**Solution notes.**

*Exercise 1.* Strong rankings put audit-log protection, leave-organisation denial and a region restriction near the top because they prevent severe harm with low friction and are easy to test. Expect weaker candidates (instance-family restrictions, mandatory naming rules) to rank low. Marks go for the explicit test (the forbidden action expecting a denial) and for noting which controls need an exception route.

*Exercise 2.* A common defensible answer is a common catalogue with an independent evidence organisation, because it limits concentration while preserving a consistent control intent. The shared management plane is justified only if you can protect the central pipeline as a crown jewel. A change trigger could be the number of organisations or an audit finding on inconsistent evidence.

*Exercise 3.* The payments service is the highest tier, the marketing website mid-tier, the sandbox lowest. Shared dependencies to examine: CI runners, registries, DNS, logging, network hubs and shared identity. A good answer either hardens such a dependency to the highest tier it serves or splits it per tier.

*Exercise 4.* Single-AZ: zone loss 1 per year × 2 h × 5,000 = 10,000; region loss 0.1 × 6 × 5,000 = 3,000; total 13,000. Multi-AZ: zone 1,000; region 3,000; total 4,000; benefit 9,000 versus 18,000 cost → net −9,000 on money alone. Warm standby: zone 1,000 (assume same as multi-AZ); region 150; total about 1,150; benefit about 11,850 versus 90,000 cost → net about −78,000. Money alone favours the cheapest option; non-financial factors such as contract penalties, regulation, safety or reputational impact, or correlated failure, could justify more. State your assumptions; they are the part that can be challenged.

*Exercise 5.* Look for: control ID, resource, reason and a duration cap; approval by control and account owner with security for data; tag-based mechanism with automated expiry; a record in the register; metrics (decision time, active count, expired, renewal rate); and a rule that three renewals trigger a design review that may produce a module with a scoped carve-out.

*Exercise 6.* Register entries should map residency to region deny, replication restriction, key location and evidence queries; exit plans to inventories of provider-specific services, export tests with egress estimates, and rebuild-as-code assessments. Gaps commonly include support access, global-service metadata and untested exports. A credible plan sequences evidence first, then tested exit for one workload, then wider scope.

*Exercise 7.* Month one: freeze new unmanaged accounts, require MFA, enable the organisation trail, alert on root and key use, inventory everything. Baseline metrics are those given. Hidden dependencies are found by 90-day audit-log queries by role, key and trust relationship; deactivate before deleting; start new guardrails in detective mode.

*Exercise 8.* Look for: an incident commander distinct from the engineer making the request; quarantine at credential, account and pipeline levels; an exception to the quarantine granted only through break-glass with a second approver, a narrow scope, a short duration and a recorded post-incident review.

*Exercise 9.* Likely causes: vending is slow and manual, baseline automation is incomplete, controls lack an exception pattern, teams see no benefit. Actions with numbers: automate vending to a median under one day, publish a pattern for the top two renewed exceptions, and offer a benefit such as central logging and cost dashboards. Verify with vending time, bypass share and renewal rate after a quarter.

## Mentoring prompts

Which three organisation-level guardrails would you deploy first, and what exceptions process would keep them from being bypassed? How would you decide between one account per environment and one per team? What would convince you that your landing zone is *used* rather than merely *documented*? A business unit asks to run its own organisation for regulatory reasons: what do you give it, what do you retain, and where does the evidence live? How would you explain to a finance director why a warm standby is or is not worth its cost? Which single dependency in your estate would, if compromised, defeat your tier separation? What would you do in the first thirty days of inheriting fifty ungoverned accounts?

---
