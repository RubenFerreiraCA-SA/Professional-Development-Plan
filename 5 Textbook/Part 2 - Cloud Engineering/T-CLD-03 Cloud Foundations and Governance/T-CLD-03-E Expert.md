# T-CLD-03-E — Expert Depth

*Chapter: [T-CLD-03 — Cloud Foundations and Governance](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-03-e"></a>
#### T-CLD-03-E — Expert Depth

**Designing an organisation for the cloud.** A landing zone is a product with users (engineering teams), an interface (account vending, baseline templates), guardrails and a support model. Account creation should be self-service with baseline configuration applied automatically: logging, identity federation, network attachment, budgets, security tooling. Break-glass access is separately controlled, monitored and tested.

**Preventive versus detective versus corrective controls.** Preventive controls (denying public storage at the organisation level) are strongest but can block legitimate work and need an exception process. Detective controls find drift but depend on response. Corrective automation (auto-remediation) is powerful and risky — it can cause outages; scope and test it. Design the exception path first, with owners and expiry.

**Failure modes of governance**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Policy sprawl | Many overlapping rules nobody understands | Few, tested, documented guardrails |
| Shadow accounts | Teams create their own to avoid friction | Make the official path easier |
| Break-glass abuse | Emergency access becomes routine | Alerting, review, rotation after use |
| Orphaned resources | No ownership or expiry | Mandatory tags, scheduled reports, automatic expiry |
| Compliance by screenshot | Manual evidence | Continuous, automated checks |
| Concentration risk | One account or region holds everything | Backup accounts, cross-region copies of critical data |

**Resilience at the provider level.** Understand blast-radius boundaries: availability zone, region, account, provider. Decide per workload the failure you design for and the one you accept; test it. Multi-region is expensive and complex — justify with business impact analysis (recovery time and recovery point objectives), not fashion. Beware hidden shared dependencies (global control planes, identity services, DNS).

**Cost as an architectural property.** Cost behaves like latency: it appears from design decisions and compounds. Include cost in design reviews, set unit-cost targets (cost per request or per customer), and treat unexplained cost changes as incidents. Weigh commitment discounts against flexibility and consider exit costs (data egress, proprietary service coupling) when assessing lock-in.

**Choosing the first three guardrails: a defensible method.** Do not start from a list of every best practice; start from the loss each guardrail prevents, the cost of false positives and whether the control can be bypassed.

| Candidate guardrail | Prevents | Cost if wrong | Good first-wave? |
| --- | --- | --- | --- |
| Deny disabling audit logging and deleting log archives | Loss of evidence after a compromise | Almost none; legitimate work does not need it | Yes |
| Restrict permitted regions | Shadow resources in unused regions; data-residency breaches | Occasional blocked experiment | Yes, with an exception path |
| Deny leaving the organisation and deleting the account's baseline roles | Accounts escaping governance | Almost none | Yes |
| Deny public object storage (account-level block) | Data exposure | Breaks legitimate public websites | Yes, with a documented exception route for approved public buckets |
| Require a specific instance family | Cost consistency | High friction, little risk reduction | No |

Order by (risk prevented) ÷ (friction caused) and by how cheaply you can prove the control works. Each guardrail should have a test that tries the forbidden action in a sandbox account and expects a deny; that test is the evidence.

**Exception path as a designed system.**

```text
Request:   control ID, account, resource, reason, requested duration (max 90 days)
Approval:  control owner + account owner; security approves anything touching data
Mechanism: time-boxed policy attachment or tag-based condition; auto-removed at expiry
Record:    stored in the register with owner, compensating control, expiry
Review:    list of active exceptions reviewed monthly; renewals need fresh justification
```

Measure the path: median time to decision, number of active exceptions, exceptions past expiry (target zero) and the share that became permanent changes to the guardrail itself (a signal that the control is wrong).

**Account-per-environment versus account-per-team: a comparison.**

| Dimension | Account per environment (dev, staging, prod) | Account per team (and environment) |
| --- | --- | --- |
| Blast radius | Large within an environment: any team can affect another's resources in prod | Small: team boundaries match account boundaries |
| Cost attribution | Needs strict tagging to attribute spend to teams | Natural: the account's bill belongs to the team |
| Operational overhead | Low: few accounts | High without automation: many baselines to maintain |
| Access control | Complex permission conditions within shared accounts | Simpler: grant per account |
| Shared service reach | Easy | Needs cross-account patterns (networking, DNS, identity) |
| Best fit | Small organisations, few teams | Larger organisations with mature account vending |

A common middle path is a workload account per team per environment (or per product) for production and shared accounts for non-production experiments, because the compounding factor is how cheaply you can vend and baseline an account. If creating an account takes two weeks and a ticket, teams will share accounts regardless of what the standard says.

**Failure modes with measurable defences**

| Failure | Measure that it is happening | Defence with a number |
| --- | --- | --- |
| Policy sprawl | Number of policies per account; time to explain why a request was denied | Fewer, composable controls; every control has an owner, test and review date; target: any deny explained in under 15 minutes |
| Shadow accounts | Accounts outside the organisation found via billing or SSO audits | Deny leaving the organisation; quarterly reconciliation of billing contacts; zero unmanaged accounts |
| Break-glass abuse | Break-glass logins per quarter | Alert on every use; rotation after use; review within 24 hours; target: use only for declared incidents |
| Orphaned resources | Resources without `owner` and `expires` tags | Daily report; auto-stop of non-production resources after expiry; target: under 2% untagged spend |
| Compliance by screenshot | Evidence older than its control's check period | Automated checks that produce time-stamped results |

**Multi-region as a decision, with numbers.** Suppose `orders-api` earns about 2,000 per hour and is down for a regional outage once every five years for about four hours. Expected loss is roughly 8,000 per five years, or 1,600 per year. A warm standby costing 60,000 per year is not justified by that alone; a regulatory requirement or reputational impact might justify it, and backup-and-restore in another region (cheaper, with an RTO of hours) may cover most of the risk. Include hidden shared dependencies in the analysis: if identity, DNS or the deployment pipeline sits in the failed region, the "standby" cannot be operated. Then test the failover yearly, otherwise the cost buys only a belief.

**Unit cost and exit cost.**

| Metric | How to compute | Use |
| --- | --- | --- |
| Unit cost | Monthly attributable cost ÷ business unit (orders, active customers) | Spot design regressions; compare architectures |
| Commitment coverage | Share of steady-state usage under commitment discounts | Avoid paying on-demand for predictable load, or over-committing |
| Exit cost | Data egress + re-engineering of proprietary services + team learning | Informs lock-in decisions; compare against the benefit of managed services |

Lock-in is not automatically bad. Ask what the proprietary service gives you, what leaving would cost today, and whether a portability layer (open protocols, standard databases, containers) is cheaper than the risk it reduces. Record the answer so it can be revisited.

**Evidence that the landing zone is used.** Share of workloads running in vended accounts; share of new accounts created by the vending path rather than by hand; median time to a baselined account; number of exceptions and their ages; teams that built their own parallel baseline (a sign the product failed on friction).

**Mentoring prompts.** Which three organisation-level guardrails would you deploy first, and what exceptions process would keep them from being bypassed? How would you decide between one account per environment and one per team? What would convince you that your landing zone is *used* rather than merely *documented*?

---
