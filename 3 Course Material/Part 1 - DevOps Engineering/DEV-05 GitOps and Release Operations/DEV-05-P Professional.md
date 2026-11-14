# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-018**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-018](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-05-P — GITOPS AND RELEASE OPERATIONS — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Repository layout (monorepo, separate desired-state repository, app-of-apps) and ownership lists; Helm versus Kustomize; least-privilege controllers; secrets in GitOps (Sealed Secrets, SOPS, External Secrets); data-migration limits of rollback (expand/contract); progressive delivery baselines; day-two operations (pod-kill impact, autoscaling, backups and recovery order); runbooks; and Argo CD/Flux mapping.

**Out of scope:** Introductory GitOps concepts and controller installation (`DEV-05-B`, `DEV-05-I`), and reconciliation theory, multi-tenancy, DR levels and canary analysis in depth (`DEV-05-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Choose and record a repository layout (monorepo, separate desired-state repository, app-of-apps), who approves production, whether auto-sync, prune and self-heal are on, how digests are updated, and which system owns each resource, avoiding two controllers managing one object.
2. Choose between Helm and Kustomize for a stated need and avoid two parallel sources of truth for one Deployment.
3. Apply least privilege to the controller (namespaced permissions, read-only Git credentials, stricter code-owner rules for production) and manage secrets without committing plaintext Secret manifests (Sealed Secrets, SOPS or External Secrets).
4. State the hard limit of GitOps rollback: reverting manifests does not reverse an incompatible data migration, so use expand/contract; and describe what a rolling update plus Git rollback gives and what canary analysis would add.
5. Run day-two operations with evidence: kill a pod under client load and measure client-visible impact, demonstrate (not merely configure) autoscaling where used, state the recovery order (cluster, controller credentials, reconcile from Git, then data), and write the runbook; prepare the evidence for **PRJ-019**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-05-P — GitOps and Release Operations — Professional](../../../5%20Textbook/Master%20Textbook.md#t-dev-05-p)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-05` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **GitOps and Release Operations — Professional** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Write a layout decision (a short ADR) covering repository model, production approvers, sync/prune/self-heal settings and digest update path, plus an ownership list of at least six resource classes with exactly one owner each.
2. Write the secret-handling design: where each secret lives, who rotates it, what is in Git (only references or encrypted material) and how you verify no plaintext Secret manifests exist.
3. Run a reviewed promotion of one digest to staging and production and an audited rollback (`git revert <sha>`). Show the commit SHAs and controller output and that no new image was built.
4. Run a client loop (for example repeated `curl` with failure counting) while deleting a pod. Report failures observed and what that says about readiness probes and replica count.
5. Write a runbook with sections for failed rollout, stalled reconciliation, secrets and data. Include why `git revert` does not restore data and the recovery order after a cluster loss.

**Pass criteria — all of the following must hold:**

- Each resource has exactly one owner and production approval is stricter than staging.
- No plaintext secrets are in Git; the design names a mechanism and a rotation owner.
- The promotion is a reviewed change to desired state only, and rollback is a recorded-SHA revert with no rebuild.
- Client-visible impact is measured rather than inferred from a new pod appearing.
- The runbook states the data limit of rollback and the recovery order.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-019 — Promote and recover an application revision** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-019).

Evidence to record: a reviewed promotion, an audited rollback and a runbook, none requiring a rebuild of the image, plus every item under *Completion criteria* on that project step. Record **PRJ-019** as **Completed** in your progress record before opening the next module.
