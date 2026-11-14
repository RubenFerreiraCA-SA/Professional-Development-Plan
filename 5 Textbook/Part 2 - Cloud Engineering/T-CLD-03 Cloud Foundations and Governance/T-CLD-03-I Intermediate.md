# T-CLD-03-I — Intermediate Practice

*Chapter: [T-CLD-03 — Cloud Foundations and Governance](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-03-i"></a>
#### T-CLD-03-I — Intermediate Practice

**Account structure and identity.**

| Identity | Use |
| --- | --- |
| Root user | Account recovery and rare break-glass tasks; MFA on, no access keys |
| Human identity (single sign-on role or IAM user) | Day-to-day work, MFA required |
| Workload role | Services and CI — no long-lived human keys |

If the only way to make a service work is an administrator key on disk, the foundation is incomplete.

**Budgets and guardrails first.** Create a monthly budget with an alert at a low threshold, before networks or compute. Document: monthly budget, thresholds, notification address, idle policy ("stop or destroy within N hours of finishing a lab"), and forbidden-by-default items (always-on NAT gateways, public databases, unused load balancers).

**Tagging.** Require a few consistent tags: `Project`, `Owner`, `Environment`, and optionally `CostCenter` and `ExpiryDate`. Tags drive cost reports, cleanup and ownership.

**Foundational services map**

| Concern | Local | Cloud foundation |
| --- | --- | --- |
| API process | Container | Container service or virtual machines |
| Image storage | Local registry | Managed container registry |
| Data | Database container | Managed database or deferred |
| Edge | localhost port | Load balancer plus security groups |
| DNS | hosts file | Managed DNS or load-balancer name |
| Logs | Console | Central log service |
| Workload identity | n/a | Task or instance role |
| Human demo access | n/a | A limited operator role |

Prefer linking existing infrastructure-as-code resources over recreating them in a console.

**An ADR for the landing zone.** Record: accounts and organisation structure, identity approach, region(s), network ranges, logging destination, cost controls, teardown policy and the reason for each.

**Teardown policy.** Write an ordered teardown (runtime, then network, then data, never the state or identity foundations while dependents exist), list what must not be deleted (budgets, MFA, audit logs) and how to confirm the bill goes quiet.

**Exercise.** Write the foundation documents for a training account: identity baseline, cost guardrails, services map and teardown runbook, each under one page.
