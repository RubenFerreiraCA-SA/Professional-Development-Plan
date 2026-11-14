# Cloud Engineering

**Estimated study time:** 128–160 hours  
**Scope:** Linux and networking for operators, AWS foundations, and secure resilient architecture for Harbour.

Cloud Engineering teaches you to **place and operate** the Harbour delivery system on intentional cloud foundations: reachability, identity, networking, resilience and cost. It builds on DevOps (where you already touched ECS/Terraform and kind) without replacing later Platform Engineering Kubernetes depth.

## Discipline objectives

1. Diagnose and restore connectivity to Harbour using Linux and network fundamentals.  
2. Establish a least-privilege AWS landing zone with billing/guardrail awareness.  
3. Design and verify a resilient, cost-conscious architecture for the sample service.  
4. Explain shared responsibility, blast radius and what must never be “temporary forever” in a training account.

## Modules

| Module | Focus | Estimated study time | Evidence of capability |
| --- | --- | ---: | --- |
| [C01 — Linux, Networking and Cloud Fundamentals](C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md) | Host ops, IP/DNS/TLS, cloud concepts, reachability runbooks | 32–40 hours | Connectivity failure diagnosed and restored from written notes |
| [C02 — AWS Cloud Foundations](C02%20AWS%20Cloud%20Foundations.md) | Accounts, IAM, VPC edge, billing, foundational services | 32–40 hours | Harbour in a documented landing zone without standing admin for the demo path |
| [C03 — AWS Infrastructure and Architecture](C03%20AWS%20Infrastructure%20and%20Architecture.md) | HA, networking patterns, data protection, limits, cost | 64–80 hours | Injected failure recovered per ADR without unrecorded console snowflakes |
| **Total** | **3 modules** | **128–160 hours** | **Intentional cloud foundations for Harbour** |

Hour ranges are **planning assumptions**. Completion is demonstrated capability, not calendar time.

## Curriculum progression

1. **C01** — Make the path to Harbour diagnosable on a host and network.  
2. **C02** — Land in AWS with identity, network edge and cost awareness.  
3. **C03** — Architect for failure, recovery and honest cost/limit trade-offs.

**Relationship to DevOps:** D05/D06 already used AWS and kind for delivery labs. Cloud Engineering revisits those layers with **breadth and judgement** (why this VPC, this IAM boundary, this AZ strategy). Do not redo D05 as a copy-paste; deepen and systematise.

## Practical outcomes and Final Project

Track Harbour increments on the [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) rows C01–C03. **End of Cloud** milestone: Harbour runs on intentional foundations with clearer IAM, networking, resilience and cost boundaries.

## Completion criteria

- Each module’s Practical Assessment at **Competent** or better.  
- Checklist C01–C03 acceptance criteria met (or honestly `Adapted:`).  
- No standing production secrets in the training account; teardown/budget notes exist.

## Learning content status

| Artifact | Status |
| --- | --- |
| This overview + module course-detail | Authored progressively with the textbook |
| Textbook chapters | [C01](../../4%20Study%20Materials/4.2%20Cloud%20Engineering/C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md), [C02](../../4%20Study%20Materials/4.2%20Cloud%20Engineering/C02%20AWS%20Cloud%20Foundations.md), [C03](../../4%20Study%20Materials/4.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md) |
| Clean-room lab certification | Separate QA workstream (same rule as DevOps) |

**Previous discipline:** [DevOps syllabus](../3.1%20DevOps/D00%20DevOps%20Syllabus.md) · **Next module:** [C01](C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md)
