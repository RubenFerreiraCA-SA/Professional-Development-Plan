# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-009**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-009](../../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-03-I — CI/CD AND BUILD AUTOMATION — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Delivery stages and their different trust levels (pull-request validation, post-merge release, promotion); deterministic validation; path filters versus required checks and the always-running gate job; releasing once and promoting by digest; flaky-test handling; and troubleshooting pipelines by fault class.

**Out of scope:** Hardening CI as a privileged system, OIDC, trusted release workflows, reusable-workflow governance (`DEV-03-P`), and provenance and pipeline threat modelling (`DEV-03-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Describe the three delivery stages (PR validation, post-merge release, promotion) and state for each whether it may run untrusted code, publish artifacts and deploy.
2. Build deterministic validation: pinned dependencies with a lock file, a clean runner, lint and tests, reports uploaded on failure, and no registry or deployment secrets in that job.
3. Explain the monorepo path-filter trap (a required check that never ran stays pending) and implement an always-running gate job that fails if a needed job failed or was skipped by mistake.
4. Release once and promote by digest: build the image once on the protected branch, record commit SHA ↔ registry digest, scan that digest, and promote with a change that only edits a `@sha256:` reference validated by a guard script.
5. Troubleshoot pipeline failures by class (test regression, dependency install failure, cache inconsistency, registry auth failure, bad promotion) from logs alone, handle flaky tests with explicit quarantine, and prepare the evidence for **PRJ-010**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-03-I — CI/CD and Build Automation — Intermediate](../../../../5%20Textbook/Master%20Textbook.md#t-dev-03-i)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-03` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **CI/CD and Build Automation — Intermediate** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Create a pull-request workflow with pinned dependencies, lint, tests, an uploaded report that runs even on failure, and `permissions: contents: read`. Show a red run blocking a merge on a deliberately failing test.
2. Add a path filter to a two-component repository. Show the pending-forever failure with a naive required check, then fix it with a gate job. Paste the gate job and the run outcomes for a docs-only change and an app change.
3. Write the guard script (or specify its rules) that accepts exactly one image reference containing `@sha256:` and 64 hex characters and rejects tags, `:latest` and multiple references. List the test cases that prove it.
4. Inject two different faults on disposable branches (for example a bad dependency pin and a failing test). Diagnose each from logs alone and write a short failure report with symptom, class, cause, fix and prevention.
5. Explain in writing why rebuilding the same commit for staging and for production yields two different artifacts, and what you do instead.

**Pass criteria — all of the following must hold:**

- The validation job is deterministic, read-only and demonstrably blocks the merge when red.
- The gate job always reports and distinguishes legitimately skipped jobs from failed ones.
- The guard rules cover the stated rejection cases and include both passing and failing tests.
- Failure reports identify the correct class from log evidence, not by guessing, and avoid blind retries.
- The rebuild answer states that each rebuild is a different artifact and that promotion changes a pointer, not the source.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-010 — Implement reviewed-change validation** in the [Project Document](../../../../4%20Project%20Document/Project.md#prj-010).

Evidence to record: the workflow file, a red check that blocked a merge and a green check after the fix, plus every item under *Completion criteria* on that project step. Record **PRJ-010** as **Completed** in your progress record before opening the next module.
