# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-008**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-008](../../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-03-B — CI/CD AND BUILD AUTOMATION — BEGINNER

### 1. Topic and Scope

**In scope for this level:** What pipelines are for; vocabulary (CI, CD as delivery versus deployment, pipeline/workflow, trigger, job, runner, artifact, required check); reading a minimal pull-request workflow (`on`, `permissions`, `runs-on`, steps); making code testable; and the habit that a failing required check blocks a merge.

**Out of scope:** Path filters and gate jobs, release and promotion workflows, OIDC, provenance and pipeline threat models. These belong to `DEV-03-I`, `DEV-03-P` and `DEV-03-E`; wiring a real pipeline into the Harbour repository belongs only in the Project Document.

### 2. Learning Objectives

1. Define CI, continuous delivery versus continuous deployment, pipeline/workflow, trigger, job, runner, artifact and required check, and explain what problem a pipeline solves compared with building on a laptop.
2. Read a minimal pull-request validation workflow top to bottom: when it runs (`on`), what it may do (`permissions: contents: read`), where it runs (`runs-on`) and what each step does.
3. Write a small automated test for a service health endpoint, run it locally before wiring it into CI, and install from pinned dependencies so today's build matches yesterday's.
4. Explain why a failing required check blocks merge and why "retry until green" is not a fix.
5. Explain why a validation job must not hold credentials to publish anything, and prepare the evidence for **PRJ-009** (a documented, repeatable build and local check).

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-03-B — CI/CD and Build Automation — Beginner](../../../../5%20Textbook/Master%20Textbook.md#t-dev-03-b)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-03` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **CI/CD and Build Automation — Beginner** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Annotate a sample workflow (given or your own) line by line: for each of `name`, `on`, `permissions`, `jobs`, `runs-on` and each step, write one sentence on what it does and what could go wrong if it were changed.
2. Write a test for a `/health` endpoint, run it locally, then break the test or the code on a branch and show the failure message. Restore it and show a pass.
3. Write the exact command sequence (create a virtual environment, install pinned dependencies, run tests, build an image) that another person could run from a clean checkout. Run it from a fresh clone and report the result.
4. Written answers: (a) What is the difference between continuous delivery and continuous deployment? (b) Why should a validation job have read-only permissions? (c) Why is re-running a flaky failing job until it passes dangerous?

**Pass criteria — all of the following must hold:**

- The annotation correctly separates trigger, permissions, environment and steps, and notes that a read-only validation job cannot publish.
- The test fails for the right reason when broken and passes when restored, with output shown.
- The command sequence works from a fresh clone without undocumented steps.
- Answers distinguish delivery from deployment and identify that retrying can mask a real intermittent fault.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-009 — Document a repeatable build and local check** in the [Project Document](../../../../4%20Project%20Document/Project.md#prj-009).

Evidence to record: the written build specification, the test file and the clean-clone run transcript, plus every item under *Completion criteria* on that project step. Record **PRJ-009** as **Completed** in your progress record before opening the next module.
