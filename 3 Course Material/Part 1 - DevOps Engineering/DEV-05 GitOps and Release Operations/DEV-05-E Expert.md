# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-019**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-019](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-05-E — GITOPS AND RELEASE OPERATIONS — EXPERT

### 1. Topic and Scope

**In scope for this level:** Reconciliation theory (eventual consistency, idempotency, ordering, field ownership); trust-boundary design for pull-based delivery; multi-tenancy and scale; promotion and environment topology (branch-, directory- or repository-per-environment); disaster-recovery levels and what Git cannot restore; failure catalogues; and progressive delivery with canary analysis.

**Out of scope:** Controller installation, drift handling, layout and secrets for a single service and day-two runbooks (`DEV-05-I`, `DEV-05-P`); implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Explain a reconciler as an eventually consistent control loop and derive the consequences: explicit ordering (`dependsOn`, health checks, sync waves), idempotent actions, field-ownership conflicts between controllers, and false confidence from weak health checks.
2. Design the trust boundary of pull-based delivery: production credentials stay in the environment, CI holds no cluster-admin, promotion is a reviewed Git write, source credentials are read-only, tenant reconcilers are namespace-scoped, and the desired-state repository is protected more strictly than application code.
3. Compare environment topologies (branch-, directory- or repository-per-environment) and multi-tenant designs (namespace, quota, network policy, scoped reconciler service account), and keep cluster-scoped resources out of tenant paths.
4. Distinguish disaster-recovery levels (workload, cluster configuration, GitOps, platform), rehearse a rebuild from Git, time it, and list what Git cannot restore (data, secrets, CA-issued identities, registry contents).
5. Use a failure catalogue (prune deleting the wrong object, flapping, stuck reconciliation, silent success, credential sprawl, ineffective rollback) and explain what telemetry and traffic shaping canary analysis needs; design an exception process for suspending reconciliation.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-05-E — GitOps and Release Operations — Expert](../../../5%20Textbook/Master%20Textbook.md#t-dev-05-e)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-05` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **GitOps and Release Operations — Expert** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Write a short analysis of three reconciliation failure scenarios (two writers for one field; a failed dependency; a health check that always passes). For each give the symptom, the mechanism and the fix.
2. Document every credential in your GitOps flow (who holds it, scope, where stored, how rotated) and test what the controller service account can do (for example `kubectl auth can-i --list --as=...`). Answer: what still protects production if the desired-state repository maintainer's account is compromised?
3. Compare the three environment topologies in a table of review quality, drift risk and operational cost, and show the actual diff between your staging and production overlays.
4. Rebuild a disposable cluster from Git and time each recovery level you can claim. State precisely what was not restored and why.
5. Write the break-glass and suspension procedure: who may suspend reconciliation, for how long, what evidence to capture and how Git becomes the source of truth again afterwards.

**Pass criteria — all of the following must hold:**

- Failure analyses name a mechanism (ordering, ownership, weak health) rather than only restating the symptom.
- The credential inventory is complete, permissions are verified by command, and the compromise answer names controls not dependent on one account.
- The topology comparison states trade-offs and evidence from your own repository.
- Only recovery levels actually demonstrated are claimed, and Git's limits are listed.
- The suspension procedure is time-boxed, audited and ends with a return to Git ownership.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-020 — Explain operational control boundaries** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-020).

Evidence to record: the control-boundary analysis, the DR rehearsal record and the break-glass procedure, collected in an ADR, plus every item under *Completion criteria* on that project step. Record **PRJ-020** as **Completed** in your progress record before opening the next module.
