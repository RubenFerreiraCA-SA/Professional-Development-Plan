# P02 — Kubernetes Administration and Operations

| | Details |
| --- | --- |
| **Estimated study time** | 48–60 hours |
| **Prerequisites** | [P01](P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md) Competent (or equivalent Harbour workloads on a disposable cluster). |

**Purpose:** Day-2 administration — RBAC, quotas, policy, incidents, recovery and upgrade rehearsal.

## Module overview

A platform that only deploys once is incomplete. P02 trains **operable** clusters: who can do what, how noisy neighbours are constrained, how policy rejects unsafe shapes, and how you recover when nodes, namespaces or desired state fail. Prefer disposable clusters; never run destructive drills against shared production.

## Learning outcomes

1. Create an unprivileged identity and prove Forbidden outcomes for out-of-scope admin actions.  
2. Apply ResourceQuota/LimitRange and at least one admission or network policy with enforcement evidence.  
3. Complete a blind or semi-blind incident drill using only runbooks and cluster evidence.  
4. Rehearse drain/PDB, namespace rebuild from Git, and a control-plane or node upgrade drill with timings.  
5. Document what a rebuild does **not** restore (PVCs, imperative Secrets, external identities).

## Suggested activities

| Activity | Estimated hours |
| --- | ---: |
| RBAC and unprivileged identity proofs | 10–12 |
| Quotas, LimitRange, Pod Security, NetworkPolicy | 10–12 |
| Incident drill and responder runbook | 8–10 |
| Drain, rebuild, upgrade rehearsal | 10–12 |
| Practical Assessment | 8–10 |
| **Total** | **48–60** |

## Practical labs and deliverables

- Ops runbook for at least one day-2 operation.  
- RBAC evidence (allowed vs Forbidden).  
- Quota/policy enforcement proof.  
- Recovery or upgrade exercise with measured steps and residual risks.

## Assessment and completion criteria

**Scenario:** Day-2 operations for Harbour’s cluster.

**Acceptance (Competent):** Complete a documented day-2 operation (e.g. quota, backup/restore, upgrade drill); an unprivileged identity cannot perform out-of-scope admin actions; honesty about non-recoverable state.

**Evidence:** Ops runbook, RBAC/quota evidence, recovery exercise — Checklist P02.

## Certifications (optional)

CKA aligns loosely with day-2 topics; not required for completion.

**Textbook:** [Chapter 2 — Kubernetes Administration and Operations](../../4%20Study%20Materials/4.4%20Platform%20Engineering/P02%20Kubernetes%20Administration%20and%20Operations.md)

**Previous:** [P01](P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md) · **Next:** [P03](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md)
