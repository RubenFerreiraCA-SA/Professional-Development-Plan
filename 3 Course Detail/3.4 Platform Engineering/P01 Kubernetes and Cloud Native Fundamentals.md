# P01 — Kubernetes and Cloud-Native Fundamentals

| | Details |
| --- | --- |
| **Estimated study time** | 48–60 hours |
| **Prerequisites** | Harbour container contract from D03; GitOps familiarity from D06 helpful. kind (or equivalent) available. |

**Purpose:** Cluster concepts, workloads, networking, probes, resources and packaging — so Harbour recovers under its workload definition alone.

## Module overview

D06 used Kubernetes enough for declarative sync. P01 makes you responsible for **correct workload behaviour**: readiness vs liveness, resource limits, Services/DNS, packaging (Kustomize/Helm) and digests. A kind multi-node cluster teaches scheduling and failover *behaviour*; it does **not** prove production HA or multi-AZ resilience.

## Learning outcomes

1. Explain Pods, Deployments, Services, Namespaces and controllers as an operations model.  
2. Configure startup, liveness and readiness probes and show what each failure mode looks like.  
3. Set requests/limits and demonstrate OOM or throttling symptoms vs application bugs.  
4. Package Harbour for the cluster (manifests and Kustomize or Helm) with digest-addressed images.  
5. After a deliberate pod kill, show the service recovers under the workload definition alone.

## Suggested activities

| Activity | Estimated hours |
| --- | ---: |
| Cluster model, kind lab baseline, local registry | 8–10 |
| Deployments, probes, resources, Secrets limits | 12–14 |
| Services, DNS, Network basics (no false HA claims) | 8–10 |
| Packaging (Kustomize/Helm) and digests | 8–10 |
| Recovery lab + Practical Assessment | 8–12 |
| **Total** | **48–60** |

## Practical labs and deliverables

- Kind (or equivalent) cluster notes and ADR for runtime choice.  
- Harbour Deployment/Service with probes and resources.  
- Packaging choice ADR; digest-pinned image evidence.  
- Pod-kill recovery demo with in-cluster or scripted client evidence (not only `port-forward` as “availability”).

## Assessment and completion criteria

**Scenario:** Prove Harbour is a sound Kubernetes workload.

**Acceptance (Competent):** Workloads become Ready with configured probes; after a pod kill, the service recovers under the workload definition alone; digests and probe behaviour are documented; HA is **not** claimed for a single-machine kind lab.

**Evidence:** Manifests/Helm/Kustomize, probe/resource settings, recovery demo notes — aligns with [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) P01.

## Certifications (optional)

CKA/CKAD-style objectives may reinforce vocabulary; they are **not** required for module completion. Check current CNCF syllabuses yourself.

**Textbook:** [Chapter 1 — Kubernetes and Cloud-Native Fundamentals](../../4%20Study%20Materials/4.4%20Platform%20Engineering/P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md)

**Previous:** [Platform syllabus](P00%20Platform%20Syllabus.md) · **Next:** [P02](P02%20Kubernetes%20Administration%20and%20Operations.md)
