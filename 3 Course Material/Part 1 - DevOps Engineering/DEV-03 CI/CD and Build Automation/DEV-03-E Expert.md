# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-011**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-011](../../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-03-E — CI/CD AND BUILD AUTOMATION — EXPERT

### 1. Topic and Scope

**In scope for this level:** Provenance and attestations (what they prove and do not prove), supply-chain frameworks such as SLSA used as a planning ladder, a pipeline threat model (poisoned pipeline execution, cache poisoning, third-party action compromise, self-hosted runner persistence, artifact substitution, script injection), flake economics and pipeline latency budgets, push-versus-pull deployment architecture and progressive delivery, and governed exceptions.

**Out of scope:** Pipeline basics, validation and release mechanics, and OIDC/hardening of a single workflow (`DEV-03-B`, `DEV-03-I`, `DEV-03-P`); implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Explain what a provenance attestation proves (this digest was built by this workflow from this commit) and what it does not (the source is benign; a compromised pipeline can sign anything), and specify a verification that binds digest, source repository, approved workflow identity and protected-branch commit.
2. Use a supply-chain framework such as SLSA as a ladder for planning: place a current pipeline on it, identify the next rung and justify climbing only where the risk warrants it.
3. Build a pipeline threat model covering poisoned pipeline execution, cache poisoning, third-party action compromise, self-hosted runner persistence, artifact substitution between jobs and script injection through untrusted inputs, with a mitigation and an evidence test for each.
4. Treat the pipeline as a product: define latency, queue time, flake rate and cost measures, set an explicit bounded retry policy, and decide which suites move to merge or nightly lanes without letting a failure there bypass release gating.
5. Decide between push-based and pull-based deployment and between progressive strategies (rolling, blue/green, canary) with their credential and health-signal consequences, and design a governed exception process with owner, compensating control and expiry.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-03-E — CI/CD and Build Automation — Expert](../../../../5%20Textbook/Master%20Textbook.md#t-dev-03-e)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-03` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **CI/CD and Build Automation — Expert** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Draw the trust boundary of a pipeline (sources, runners, caches, registries, deployment target) and mark every point where untrusted data crosses it. For each of the six threat classes name the crossing point it exploits.
2. For each threat class write one mitigation and one test you could run to show the mitigation works (for example a workflow that interpolates a PR title into a shell command, and its environment-variable fix).
3. Write the verification policy for a deployable artifact: which facts must be checked (digest, repository, workflow identity, branch, commit) and what the check still cannot detect. Include the answer to "what could a compromised build system still do?"
4. Write a one-page design comparing push and pull deployment (credentials held by CI, audit trail, rollback) and state which you would choose for the Harbour system and why.
5. Write an exception policy for a critical vulnerability with no fix: approver, compensating control, expiry and review trigger.

**Pass criteria — all of the following must hold:**

- The boundary diagram identifies every untrusted input, and each threat is mapped to a specific crossing point.
- Mitigations are testable and tests are concrete; script injection is mitigated by passing inputs via environment variables.
- The verification policy binds several facts together, not a signature alone, and names residual risk.
- The push/pull design addresses credential exposure and audit, not just convenience.
- The exception policy has an owner and an expiry; open-ended exceptions fail the criterion.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-012 — Evaluate supply-chain and promotion controls** in the [Project Document](../../../../4%20Project%20Document/Project.md#prj-012).

Evidence to record: the threat model, the rejected unsafe promotion and the architecture decision record, plus every item under *Completion criteria* on that project step. Record **PRJ-012** as **Completed** in your progress record before opening the next module.
