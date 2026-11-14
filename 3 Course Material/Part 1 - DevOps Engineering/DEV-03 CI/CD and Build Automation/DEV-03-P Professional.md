# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-010**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-010](../../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-03-P — CI/CD AND BUILD AUTOMATION — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Treating CI as a privileged system (least-privilege tokens, fork pull requests, `pull_request_target`, ephemeral runners, pinning third-party actions by commit SHA, permission matrices); short-lived cloud credentials with OIDC; a trusted release workflow that builds once and records evidence; testable promotion guards and rollback by previous digest; reusable workflows; and merge-gate design.

**Out of scope:** Provenance verification, supply-chain frameworks, pipeline threat modelling beyond forks, flake economics and push-versus-pull deployment architecture (`DEV-03-E`); basic pipelines and gate jobs (`DEV-03-B`, `DEV-03-I`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Treat CI as a privileged system: apply `permissions: contents: read` on validation, avoid `pull_request_target` combined with checkout of untrusted code, keep secrets from fork pull requests, use ephemeral runners for untrusted code, pin third-party actions by commit SHA, and maintain a permission matrix (workflow × token scope × secrets × triggers).
2. Replace long-lived cloud keys with OpenID Connect: write a trust policy constrained by audience (`aud`) and subject (`sub` for repository plus environment or branch) and explain why wildcards are unacceptable.
3. Design a trusted release workflow that triggers only on the protected branch, uses an environment with protection, builds once, pushes, captures the registry digest, and records commit SHA, digest, workflow run URL and scan or SBOM output for that digest.
4. Treat promotion as code: write a unit-tested guard that extracts exactly one `@sha256:` reference and rejects mutable tags and multiple references, and roll back by promoting a previously recorded digest without rebuilding.
5. Extract common steps into a versioned reusable workflow with a change policy, and design the merge gate (reviews plus an always-reporting required check), documenting any gap the hosting plan cannot enforce together with a compensating control.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-03-P — CI/CD and Build Automation — Professional](../../../../5%20Textbook/Master%20Textbook.md#t-dev-03-p)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-03` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **CI/CD and Build Automation — Professional** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Produce a permission matrix for three workflows (PR validation, release, promotion verification): trigger, token scopes, secrets, environment, and which refs may run them. Highlight any cell that gives untrusted code a privilege and explain how you removed it.
2. Write an OIDC trust policy for a role used only by the release workflow, scoped to your repository and the `release` environment. Explain what an attacker with a pull request could and could not do with it.
3. Write the release workflow and a sample `release-evidence.txt` for one release (commit SHA, digest, run URL, scan result). State how a reviewer would later verify that a deployed digest came from this run.
4. Write the guard script and at least six test cases (one valid, and invalid cases: tag-only, `:latest`, two references, short digest, empty file). Describe how a rollback is performed using this mechanism.
5. Write a design note on the merge gate: required checks, reviewers, how path-filtered jobs still report, and what you would do if the plan could not enforce a required check.

**Pass criteria — all of the following must hold:**

- No untrusted trigger receives write scope or a secret; actions are pinned by SHA; the matrix is consistent with the workflow files.
- The trust policy contains explicit `aud` and `sub` constraints with no wildcard and the explanation states the residual risk.
- The release evidence links commit, digest, run and scan to the same artifact, and the release does not rebuild for promotion.
- The guard tests include every invalid case listed, and the rollback uses a prior digest, not a rebuild.
- The merge-gate design includes an always-reporting check and honestly documents any unenforceable control.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-011 — Produce a traceable release** in the [Project Document](../../../../4%20Project%20Document/Project.md#prj-011).

Evidence to record: the release run, the recorded commit-to-digest evidence and the promotion hand-off file, plus every item under *Completion criteria* on that project step. Record **PRJ-011** as **Completed** in your progress record before opening the next module.
