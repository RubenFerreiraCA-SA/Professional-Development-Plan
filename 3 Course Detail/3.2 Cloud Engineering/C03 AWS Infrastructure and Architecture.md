# C03 — AWS Infrastructure and Architecture

| | Details |
| --- | --- |
| **Estimated study time** | 64–80 hours |
| **Prerequisites** | [C02](C02%20AWS%20Cloud%20Foundations.md); Terraform literacy from [D05](../3.1%20DevOps/D05%20Infrastructure%20as%20Code%20and%20Terraform.md) strongly recommended. |

## Objective

Design and verify a **resilient, cost-conscious** Harbour architecture on AWS: multi-AZ intent (or honest single-AZ limits), failure injection, backup/restore assumptions and change via code — not unrecorded console snowflakes.

## Outcomes

1. Produce an architecture ADR covering compute, network, data, edge and observability hooks.  
2. Justify HA, backup and limit choices with verified behaviour (not aspirational diagrams).  
3. Inject or simulate a documented failure mode and recover per the ADR.  
4. Keep cost controls and teardown paths explicit.  
5. Prefer IaC changes; document any break-glass console use.

## Suggested activities

| Activity | Estimated hours |
| --- | ---: |
| Architecture options and ADR | 12–16 |
| Implement/adjust infra as code | 20–24 |
| Failure injection + recovery drills | 16–20 |
| Cost, limits, Practical Assessment | 16–20 |
| **Total** | **64–80** |

## 1. Architecture decision

Compare topologies (e.g. ECS in public subnets vs private+NAT; RDS Multi-AZ vs single). Record trade-offs for **training vs production**.

## 2. Implement through code

Extend or refine D05 `infra/` — do not invent a parallel unmanaged stack. Security groups, least-privilege task roles, health checks and load balancer target groups as applicable.

## 3. Failure and recovery

Pick one: AZ impairment simulation, dependency outage, bad deploy rollback (tie D06), or restore-from-backup drill for data. Evidence must match the ADR.

## 4. Cost and limits

Service quotas, idle spend, NAT cost honesty, destroy scripts/runbooks.

## Practical Assessment — recover per ADR

**Required evidence:** Architecture ADR, verified HA/backup/limit choices in `infra/`, recovery evidence for the injected failure, cost controls, list of any console exceptions.

**Acceptance:** Checklist C03 — recovery matches the ADR without unrecorded snowflakes.

**Textbook:** [Chapter 3 — AWS Infrastructure and Architecture](../../4%20Study%20Materials/4.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md)

**Previous:** [C02](C02%20AWS%20Cloud%20Foundations.md) · **Next (optional):** [AI syllabus](../3.3%20AI%20Engineering/A00%20AI%20Syllabus.md) · **Next:** [Platform syllabus](../3.4%20Platform%20Engineering/P00%20Platform%20Syllabus.md) (after Cloud milestone)
