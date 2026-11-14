# T-CLD-03-P — Professional Engineering

*Chapter: [T-CLD-03 — Cloud Foundations and Governance](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-03-p"></a>
#### T-CLD-03-P — Professional Engineering

**Multi-account strategy.** Separate accounts (or equivalent subscriptions or projects) give hard blast-radius and billing boundaries. A common structure: a management account (billing and organisation policy only), a security or audit account (central logs), shared services, and separate non-production and production workload accounts. Apply preventive guardrails (service control policies or organisation policies) at the organisation level and detective controls (configuration rules, security findings) everywhere.

**Governance controls**

| Area | Control |
| --- | --- |
| Identity | Single sign-on, MFA, short-lived credentials, least privilege, regular access review |
| Logging | Organisation-wide audit trail to a protected, immutable store |
| Network | Standard ranges, no unreviewed internet exposure, centralised egress where required |
| Data | Encryption at rest and in transit, key ownership, classification |
| Cost | Budgets per account, anomaly alerts, tag policy, rightsizing and idle policies |
| Compliance | Evidence collection mapped to control frameworks you must meet |

**Shared responsibility as a design input.** Make a matrix for each chosen service: what the provider guarantees, what you must configure, what you must monitor and what you must prove to an auditor. Managed services remove patching but add configuration surface (public access settings, encryption options, backup retention).

**Placement decisions with trade-offs.** Record why a component is run as virtual machines, containers, serverless or a managed service: operational burden, cost at your scale, portability, performance, compliance and team skills. A topology diagram that implies high availability while a single instance runs is aspirational; either fix the diagram or the infrastructure.

**Cost engineering.**

- Forecast with the pricing calculators and verify against billing data weekly in the early period.
- Understand cost drivers: compute hours, load-balancer hours and capacity units, NAT gateway hours and per-gigabyte processing, data transfer (especially cross-AZ and out to the internet), storage tiers and request counts, managed database instance size and replicas.
- Use commitments (savings plans, reservations) only for stable baseload, after measuring.
- Add a showback or chargeback view so teams see what they spend.

**Decision guide**

| Question | Prefer | Because |
| --- | --- | --- |
| Where do human users authenticate? | Central single sign-on with MFA | Revocation and audit |
| How do services authenticate? | Roles with short-lived credentials | No long-lived keys to leak |
| How do we limit blast radius? | Separate accounts and guardrail policies | Hard boundaries |
| How do we avoid surprise bills? | Budgets, anomaly alerts, idle policy, tag enforcement | Early detection |
| How do we prove compliance? | Automated evidence from logs and configuration rules | Repeatable audits |
