# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-017**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-017](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-05-I — GITOPS AND RELEASE OPERATIONS — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Installing a GitOps controller (Flux or Argo CD) on an isolated practice cluster; bootstrap versus reconcile credentials; pointing the controller at per-environment paths; reading controller signals (source, build and health failures); promotion through Git; image pull paths for local and private registries; drift and self-heal; rollback by `git revert`; and troubleshooting.

**Out of scope:** Repository layout decisions, Helm versus Kustomize, secrets management, progressive delivery and day-two runbooks (`DEV-05-P`), and reconciliation theory, trust boundaries and DR (`DEV-05-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Install a GitOps controller on a disposable local cluster (for example `kind`), explain that bootstrap writes configuration once while reconcile only needs read access, and replace a broad bootstrap token with a read-only deploy key.
2. Create one reconciliation object per environment (`Kustomization` or `Application`) with a path, interval, prune and health wait, and explain why staging and production reconcile independently.
3. Classify controller failures as source failed (Git unreachable or bad credentials), build failed (invalid YAML or Kustomize error) or health check failed (workload not Ready), and inspect each with `flux get`, controller logs and `kubectl`.
4. Promote through Git by changing only the digest in the target overlay, verify both environments run the same digest, and explain image pull paths (`kind load docker-image` versus registry credentials and `ImagePullBackOff`).
5. Observe drift and self-heal (manual scale reverted), use suspend/resume as a time-boxed exception, roll back with `git revert` of a recorded commit, and prepare the evidence for **PRJ-018**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-05-I — GitOps and Release Operations — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-dev-05-i)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-05` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **GitOps and Release Operations — Intermediate** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Show the controller running on a local cluster, the credential it uses for Git (read-only) and how the bootstrap token was removed. Paste `flux get sources git` and `flux get kustomizations`.
2. Scale a Deployment by hand and capture the controller restoring the Git value, with timestamps. Then suspend reconciliation, make a change, show the drift remains, commit the change to Git and resume.
3. Break three things on disposable branches (an unreachable Git URL, invalid YAML, an unpullable digest). For each record which failure class the controller reported, the evidence line, and the fix.
4. Promote one digest from staging to production by a one-line pull request and show with `kubectl get deploy -o jsonpath='{..image}'` that both environments run it.
5. Roll back a deliberately broken release with `git revert <recorded sha>` and show recovery. Explain why a blind `git revert HEAD` can be wrong.

**Pass criteria — all of the following must hold:**

- The controller uses read-only repository credentials and the bootstrap token is revoked or documented as removed.
- The self-heal demonstration shows both the correction and the explicit, time-boxed suspension exception.
- Each fault is classified correctly (source, build, health) from controller output.
- The promotion diff is one line and both environments show the same digest.
- The rollback uses the recorded commit SHA and the system returns to a healthy state.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-018 — Observe reconciliation and drift** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-018).

Evidence to record: the reconciliation status output, one drift observation and the observed-versus-desired comparison, plus every item under *Completion criteria* on that project step. Record **PRJ-018** as **Completed** in your progress record before opening the next module.
