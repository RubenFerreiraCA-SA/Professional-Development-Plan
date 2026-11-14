# Platform Engineering — Textbook

*Kubernetes workloads, day-2 operations, self-service paths and an integrated platform for Harbour.*

This textbook accompanies the [Platform syllabus](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P00%20Platform%20Syllabus.md). Chapters align with modules **P01–P04**. Each `PXX` file is a chapter; numbered sections inside use the chapter number (**Section 1.1** in P01, **Section 2.1** in P02, and so on). The course-detail files remain the curriculum specifications; this book is the teaching material.

## Table of contents

| Chapter | Subject | Study material |
| --- | --- | --- |
| 1 · P01 | Kubernetes and Cloud-Native Fundamentals | [Read Chapter 1](P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md) |
| 2 · P02 | Kubernetes Administration and Operations | [Read Chapter 2](P02%20Kubernetes%20Administration%20and%20Operations.md) |
| 3 · P03 | Internal Developer Platforms and DevEx | [Read Chapter 3](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) |
| 4 · P04 | Platform Architecture and Final Project | [Read Chapter 4](P04%20Platform%20Architecture%20and%20Final%20Project.md) |

## How the chapters connect

| Chapter | Harbour gains | [Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) bar (summary) |
| --- | --- | --- |
| P01 | Sound Kubernetes workloads: probes, resources, digest-addressed images, packaging | Workloads ready with probes; after a pod kill the service recovers under the workload definition alone |
| P02 | Operable cluster: RBAC, quotas, policy, incident drills, recovery, upgrade rehearsal | A documented day-2 operation; an unprivileged identity cannot perform out-of-scope admin actions |
| P03 | Golden path and self-service | A trial user stands up a service from written docs without 1:1 help |
| P04 | Integrated, defensible platform | Every required final-demonstration item for your pathway, with ADRs |

## How to study

Complete DevOps (especially [D03](../4.1%20DevOps/D03%20Docker%20and%20Containerization.md), [D04](../4.1%20DevOps/D04%20CICD%20and%20Build%20Automation.md) and [D06](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md)) first when possible; Cloud ([C01–C03](../4.2%20Cloud%20Engineering/README.md)) supplies networking and architecture vocabulary. Work through P01 and P02 in order — P02 reuses the cluster, registry, manifests and probe client built in P01.

Labs use **kind** (a local multi-node cluster) with a local registry so images are deployed **by digest**. A kind cluster runs on one machine: it teaches scheduling, failover behaviour and operations discipline, but it does **not** demonstrate production high availability, zone resilience or control-plane redundancy. The chapters say so wherever a claim could be overstated — and ask you to record the same limits in your ADRs.

Hour estimates in course detail are planning assumptions. Use disposable clusters for destructive drills; never point these labs at shared or production clusters, and keep real secrets out of Git.

## Documentation status

| | |
| --- | --- |
| **P01–P04** | Authored; **corrections required** after audits `ff921e0`/`ea9eb06`/`65a094d` (not signed off) |
| **Remediation focus** | Fail-closed Kyverno report parse, release-manifest producer, recovery HTTP/isolation, Flux credentials+recon proof, complete policy.yml |
| **Not claimed** | Clean-room lab execution; independent Gate-5 platform-user acceptance; executable Harbour reference repository |

**Course detail:** [P00 Platform Syllabus](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P00%20Platform%20Syllabus.md) · **Checklist:** [Final Project Checklist · Platform](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
