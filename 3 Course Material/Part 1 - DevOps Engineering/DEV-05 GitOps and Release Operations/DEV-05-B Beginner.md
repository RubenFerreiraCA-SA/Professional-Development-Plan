# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-016**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-016](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-05-B — GITOPS AND RELEASE OPERATIONS — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Push versus pull delivery; desired state, live state, reconciliation, drift, prune and self-heal; who owns what (infrastructure as code, Git desired-state directory, GitOps controller, humans in an emergency); a mental run of a replica change through Git; and declarative configuration with Kustomize bases and overlays.

**Out of scope:** Installing and operating a controller, promotion, rollback and drift handling (`DEV-05-I`), repository layout, secrets, progressive delivery and day-two operations (`DEV-05-P`), and reconciliation theory and DR (`DEV-05-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Contrast push (a person or pipeline runs `kubectl`) and pull (a controller reconciles toward Git) delivery and say what each means for audit trail and for the credentials CI needs.
2. Define desired state, live state, reconciliation, drift, prune and self-heal, and apply the terms to a worked example.
3. Assign ownership: which of infrastructure as code, the Git desired-state directory, the GitOps controller and humans in an emergency owns the cluster, workload definitions, reconciliation and break-glass changes.
4. Walk through a replica change (`replicas: 2` → `3`) from pull request to merged commit to controller action, and explain what happens to a manual scale to five.
5. Write a Kustomize base with per-environment overlays that set namespace, replicas and an image digest, preview each with `kubectl kustomize`, and prepare the evidence for **PRJ-017**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-05-B — GitOps and Release Operations — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-dev-05-b)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-05` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **GitOps and Release Operations — Beginner** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Draw a diagram of the pull-based flow: author, pull request, Git, controller, cluster, with arrows labelled by what moves. Mark where CI sits and what credentials it does not need.
2. Fill in an ownership table for cluster and networks, application namespaces, Deployments/Services, controller and emergency changes, and justify each row.
3. Render the staging and production overlays of a small Kustomize layout, diff the outputs and explain each difference.
4. Explain in your own words why the overlay carries an image digest and not a tag.
5. Written answers: define drift and self-heal; explain what happens when someone scales a Deployment manually under an active controller.

**Pass criteria — all of the following must hold:**

- The diagram correctly places the controller inside the environment and shows that CI does not need cluster administrator access.
- The ownership table has exactly one owner per resource class and names break-glass as an exception returning ownership to Git.
- The rendered overlays differ only in the intended fields, and the diff is explained.
- The digest answer references immutability (a tag can move; a digest cannot).
- Definitions are accurate and the manual-scale scenario ends with the controller restoring Git's value.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-017 — Declare desired application state** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-017).

Evidence to record: the target deployment definitions and their rendered output, stored with version history, plus every item under *Completion criteria* on that project step. Record **PRJ-017** as **Completed** in your progress record before opening the next module.
