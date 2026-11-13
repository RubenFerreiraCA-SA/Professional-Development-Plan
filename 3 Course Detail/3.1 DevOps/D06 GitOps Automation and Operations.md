# D06 — GitOps, Automation and Operations

| | Details |
| --- | --- |
| **Estimated study time** | 30–44 hours |
| **Prerequisites** | [D03 — Docker and Containerization](D03%20Docker%20and%20Containerization.md), [D04 — CI/CD and Build Automation](D04%20CICD%20and%20Build%20Automation.md), [D05 — Infrastructure as Code and Terraform](D05%20Infrastructure%20as%20Code%20and%20Terraform.md). Basic familiarity with Kubernetes manifests, deployments and services; deeper Kubernetes administration is developed in P01–P02. |

## Objective

Design an **auditable, self-correcting application delivery process** driven by declarative desired state. A Platform Engineer should understand exactly what GitOps reconciles, which changes it cannot safely automate, and how teams recover when desired and actual states diverge.

## Outcomes

1. Explain reconciliation loops, desired state, drift, pull-based delivery, controller permissions and the GitOps trust model.
2. Build maintainable deployment configuration across environments using Helm, Kustomize or another justified approach.
3. Integrate CI release artifacts with GitOps promotion without granting CI unrestricted cluster privileges.
4. Demonstrate controlled rollouts, application health checks, rollback and environment recovery.
5. Establish safe day-two operations for scaling, secrets, certificate lifecycle, backups and incident response.
6. Diagnose stalled reconciliation, unhealthy workloads, configuration errors and misaligned infrastructure/application state.
7. Build platform-level guardrails that make the compliant deployment path easier than manual intervention.

## 1. Design the GitOps operating model

Contrast **imperative deployment** (`kubectl apply` or a pipeline writing live resources) with a controller continually reconciling Git-defined desired state.

Explore Argo CD or Flux and distinguish:
- The **source** repository containing application code and the **desired-state** repository or directory containing deployable configuration.
- A release artifact's immutable digest versus a mutable image tag.
- A controller's reconciliation interval, health assessment, sync status and drift handling.
- Ownership boundaries between Terraform-managed infrastructure, GitOps-managed workloads and manual emergency actions.
- The risk of giving a GitOps controller excessive cluster or secret access.

**Architecture decision:** Choose separate repositories or an environment-specific layout. Record who can approve production changes, which automation can update image references, and whether manual sync is allowed.

**Lab:** Install a GitOps controller in an isolated cluster and configure it to reconcile the Final Project service from a restricted repository. Local Kubernetes (such as kind or minikube) is acceptable; adapt infrastructure-sensitive exercises to the available environment.

## 2. Configuration and environment promotion

Provide reproducible deployment definitions:

- Define deployments, services, health probes, resource requests/limits and configuration references.
- Compare Helm templating and Kustomize overlays, including how each handles environment differences, versioning and troubleshooting.
- Keep credentials out of Git. Compare external secret operators, cloud secret managers and encrypted manifests; understand the associated key-management responsibilities.
- Protect production-specific configuration through code owners or approval rules.
- Prefer immutable image digests and record the relationship to the D04 release.

**Promotion exercise:** Build a valid release, update the test environment's declared image digest and verify it becomes the running digest. Promote **the same artifact** to another isolated environment via a reviewed configuration change.

**Drift exercise:** Change a managed resource in a sandbox directly and observe detection/reconciliation. Explain why auto-sync, pruning and self-heal should be configured deliberately, not universally enabled without understanding consequences.

## 3. Release strategies and rollback

Compare rolling updates, blue/green, canary and progressive delivery. Explain what platform-level support each strategy needs and what additional controller or ingress/traffic facilities may be required.

Design the **deployment contract**:
- Readiness versus liveness: health failures should not create cascading restarts.
- Pre-deployment checks and compatibility between the old and new application versions.
- Database schema migrations and backward compatibility: Git revert alone cannot reverse data changes safely.
- Observability and automated progression/abort decisions based on meaningful signals.
- Rollback to a **known-good manifest and digest** with a traceable change record.

**Failure drill:** Deploy an intentionally broken image/configuration. Diagnose rollout status, events, pods, probes, logs and controller state. Revert the desired-state commit and verify recovery. Demonstrate why directly patching live state is temporary under active reconciliation.

## 4. Day-two reliability and automation

A Platform Engineer must support the workload **after** the first deployment:

- Configure resource requests and limits with measured baselines.
- Demonstrate horizontal autoscaling using CPU or another appropriate metric, with capacity and limits understood.
- Plan backups, **test restores**, and define whether application data resides in the cluster or in a managed external service.
- Document certificate and credential rotation, expiration monitoring and operator ownership.
- Model dependency failures (database unavailable, network partition, exhausted capacity, unavailable image registry) and decide how the platform should respond.
- Write a runbook for a failed rollout, stalled reconciliation and a degraded service.

**Experiment:** Trigger a controlled scaling event, kill an application pod, and observe recovery. Do not equate replacement of a pod with proof of zero downtime; evaluate actual client-facing availability.

## 5. Safety, access and policy

Review the controller as a powerful service with access to clusters and configuration sources. Demonstrate least-privilege service accounts, repository authentication, namespace boundaries and admission policies where available.

Discuss when a GitOps deployment should **not** automatically prune a resource (for example persistent data or shared infrastructure). Document disaster recovery: restoring the cluster/controller, restoring secrets and state, and reattaching or restoring application data in the correct order.

Connect D05 and D06 with a clear contract: Terraform provisions clusters and foundational infrastructure; the GitOps controller manages chosen workloads. Avoid dual ownership of the same resources.

## Practical Assessment — controlled release and recovery

**Scenario:** A platform team must support frequent application releases while preventing accidental infrastructure deletion and ensuring an auditable return to a known-good version.

**Required evidence:**

1. GitOps controller connected to an isolated cluster with explicit repository, namespace and access boundaries.
2. Two application environments with declared configuration and immutable container-image references.
3. A reviewed change promoting the D04 artifact between environments, with source and deployment records.
4. A broken-release test showing detection, investigation and recovery via desired-state change.
5. A drift experiment demonstrating either reconciliation or an explicit, documented non-auto-sync policy.
6. An autoscaling/self-healing test evaluated against real service-health signals.
7. A tested operational runbook covering rollout failure, secret handling and data recovery assumptions.

**Acceptance:** A different engineer can answer **what should be running**, **what is actually running**, **why they differ** and **how to recover safely** without editing undocumented live state.

## Further learning

- [OpenGitOps principles](https://opengitops.dev/)
- [Argo CD documentation](https://argo-cd.readthedocs.io/)
- [Flux documentation](https://fluxcd.io/flux/)
- [Kubernetes — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes — Configure liveness, readiness and startup probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Kubernetes — Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

**Textbook:** [Chapter 6 — GitOps, Automation and Operations](../../4%20Study%20Materials/4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md)

**Previous:** [D05 — Infrastructure as Code and Terraform](D05%20Infrastructure%20as%20Code%20and%20Terraform.md) · **Next:** [D07 — Observability](D07%20Observability.md)
