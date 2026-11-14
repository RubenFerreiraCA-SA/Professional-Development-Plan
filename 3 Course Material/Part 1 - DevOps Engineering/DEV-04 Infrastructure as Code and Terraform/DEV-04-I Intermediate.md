# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-013**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-013](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-04-I — INFRASTRUCTURE AS CODE AND TERRAFORM — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Remote state with locking and per-environment state keys; the bootstrap problem for the state backend; variables, outputs and environment roots; modules as interfaces with input validation and `terraform test`; staged first deployments for dependent resources; handling drift; and recovering from a partially failed apply.

**Out of scope:** Plan/apply separation in CI with federated identity, policy as code, state security design and cost/teardown governance (`DEV-04-P`), and state surgery, provider governance and organisation-scale strategy (`DEV-04-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Explain why local state is not a platform and configure an access-controlled remote backend with versioning, encryption and native locking, using a different state `key` per environment, and describe the chicken-and-egg bootstrap of the state bucket.
2. Demonstrate that locking works (a long-running apply plus a second `plan -lock-timeout=0s` showing a lock error) and explain why `force-unlock` is not a reflex.
3. Structure environments as separate root configurations (`envs/staging`, `envs/prod`) with separate state, variables and name or network prefixes, and show that the prod plan is empty after a change to staging.
4. Author a module with an explicit interface (required inputs, validation such as rejecting `0.0.0.0/0`, outputs, version constraints) and test it with `terraform test`, starting with deliberately failing cases.
5. Handle drift and partial failure: introduce drift, read the plan, decide explicitly to revert, adopt or accept, and keep a recovery log (symptom, cause, action, prevention) for a failed apply; prepare the evidence for **PRJ-014**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-04-I — Infrastructure as Code and Terraform — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-dev-04-i)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-04` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Infrastructure as Code and Terraform — Intermediate** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Show a backend configuration with encryption, state versioning and native locking and a distinct state key per environment. Explain how IAM must allow both the state object and the lock object, and how the backend itself is bootstrapped.
2. Demonstrate lock contention using a `time_sleep` resource and a second `plan -lock-timeout=0s`. Paste the lock error and describe what you checked before considering `force-unlock`.
3. Create two environment roots using one module. Change only staging, then show that prod's `plan` reports no changes and that the two state files are independent.
4. Write a module variable with a validation block that rejects open ingress, plus a `terraform test` file with a failing and a passing run. Paste the test output.
5. Tag a resource by hand (or edit a managed file) to create drift. Show the plan, choose revert, adopt or accept, and record the decision and its reason.
6. Describe how you would apply a configuration whose resources depend on each other in stages (for example network and registry first, then an image push outside Terraform, then the runtime).

**Pass criteria — all of the following must hold:**

- The backend design includes locking, encryption, versioning and an environment-specific key, and names the bootstrap procedure.
- The lock demonstration shows the lock error and the response is to find the active run rather than force-unlock.
- State isolation and the empty prod plan are shown, not just described.
- The module test fails when it should fail and passes when it should pass.
- The drift record states an explicit decision with rationale; the staged-apply description separates stages by an observable condition.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-014 — Separate environments and reuse configuration** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-014).

Evidence to record: the module, the two environment roots and the isolation evidence, plus every item under *Completion criteria* on that project step. Record **PRJ-014** as **Completed** in your progress record before opening the next module.
