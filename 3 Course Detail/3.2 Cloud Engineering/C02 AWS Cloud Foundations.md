# C02 — AWS Cloud Foundations

| | Details |
| --- | --- |
| **Estimated study time** | 32–40 hours |
| **Prerequisites** | [C01](C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md); training AWS account with billing alarm; DevOps D05 familiarity helpful but not mandatory. |

## Objective

Establish a **landing-zone foundation** for Harbour: account hygiene, IAM least privilege, VPC edge awareness, foundational services vocabulary and cost guardrails. The demo path must not depend on standing admin credentials.

## Outcomes

1. Configure and explain account/root/IAM user-role separation and MFA expectations.  
2. Sketch a minimal VPC (public/private intent, route tables, security groups) for Harbour.  
3. Place Harbour API and data stores on appropriate foundational services (cross-link D05).  
4. Apply budget alerts and basic cost visibility.  
5. Run Harbour under least-privilege identities for the documented demo path.

## Suggested activities

| Activity | Estimated hours |
| --- | ---: |
| Account, IAM, MFA, credential hygiene | 8–10 |
| VPC, SG, reachability from C01 runbook into AWS | 10–12 |
| Core services map (compute, LB, data, DNS) | 6–8 |
| Cost/budgets + Practical Assessment | 8–10 |
| **Total** | **32–40** |

## 1. Identity and account hygiene

- Root vs IAM; break-glass; MFA.  
- Roles for humans vs workloads (preview instance profiles / task roles — deepen in C03/D05).  
- No long-lived keys in Git; prefer SSO/short-lived creds where available.

## 2. Network edge

- VPC CIDR, subnets, IGW/NAT trade-offs (cost vs privacy).  
- Security groups as allow-lists; network ACLs awareness.  
- Revisit C01 hop tests against an AWS-published endpoint.

## 3. Foundational services map

Document where Harbour API, DB, logs and DNS live. Prefer linking to existing `infra/` from D05 rather than rebuilding from scratch.

## 4. Cost and guardrails

- Budgets and anomaly alerts.  
- Tagging `project=harbour`, `env=training`.  
- Destroy/idle policy for training resources.

## Practical Assessment — landing zone without standing admin

**Required evidence:** IAM/network baseline notes, architecture sketch, Harbour reachable under least-privilege demo identity, cost/guardrail proof, explicit “no admin for happy path” statement.

**Acceptance:** Checklist C02 — Harbour runs in the documented landing zone; demo path does not rely on standing admin credentials.

**Textbook:** Not yet authored (course detail ready for study planning).

**Previous:** [C01](C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md) · **Next:** [C03](C03%20AWS%20Infrastructure%20and%20Architecture.md)
