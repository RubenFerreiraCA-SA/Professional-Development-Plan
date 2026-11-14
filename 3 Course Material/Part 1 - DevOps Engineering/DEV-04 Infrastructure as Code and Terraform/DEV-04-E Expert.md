# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-015**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-015](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-04-E — INFRASTRUCTURE AS CODE AND TERRAFORM — EXPERT

### 1. Topic and Scope

**In scope for this level:** State surgery and recovery (`import`, `state mv`, `state rm`, `moved` and `removed` blocks, backups, empty plan as acceptance); replacement semantics (`create_before_destroy`, `ignore_changes`); provider and version governance (lock files, mirrors, major-version rehearsal); scaling patterns (small roots, shared module registry, workspaces, wrappers); scheduled drift detection; identity design for plan/apply/state administration; cost governance; and failure catalogues.

**Out of scope:** Beginner and intermediate workflows, a single-environment CI lane and module authoring basics (`DEV-04-B`, `DEV-04-I`, `DEV-04-P`); implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Perform and defend state surgery safely: back up state first, prefer declarative `import`, `moved` and `removed` blocks that go through review, and accept the operation only when a following plan is empty.
2. Predict and manage replacement semantics: read `# forces replacement`, use `create_before_destroy` or blue/green constructs for traffic-critical resources, and use `ignore_changes` sparingly with documentation because it hides drift.
3. Govern providers and versions: pin Terraform and provider versions, review lock-file changes like dependency updates, consider provider mirrors, and rehearse major-version upgrades in a copy of the environment.
4. Evaluate organisation-scale patterns (many small roots by lifecycle, shared module registry, workspaces, orchestration wrappers) by benefit and risk, design scheduled drift detection (`plan -detailed-exitcode`) with alerting, and separate plan, apply and state-administration identities.
5. Make cost visible and enforced (tags, budgets, idle policies, teardown tested as a feature) and use a failure catalogue (corrupt state, concurrent applies, secret leakage via plan, unreviewed access widening, bootstrap cycles, destroying shared foundations) to design defences.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-04-E — Infrastructure as Code and Terraform — Expert](../../../5%20Textbook/Master%20Textbook.md#t-dev-04-e)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-04` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Infrastructure as Code and Terraform — Expert** in your own words, without undocumented help, and keep the outputs with your progress record.

1. On a copy of a state file, move a resource between addresses with `state mv` and again with a `moved` block. Show the empty plan after each, and explain why the declarative version is preferable.
2. Change an attribute that forces replacement. Show the plan annotation, then redesign the change so the replacement is safe (for example `create_before_destroy` or an in-place alternative), and explain what `ignore_changes` would have hidden.
3. Compare at least three organisation patterns (single large root, many small roots, workspaces, wrapper/managed platform) in a table of benefit, risk and when you would choose each. Include how cross-root dependencies are managed.
4. Design a scheduled drift check: the command, how exit code 2 is handled, who is notified and what the decision procedure is. Define the three roles (plan, apply, state-admin) and the permissions each may not have.
5. Choose four failure catalogue entries and for each write the earliest detection signal and the preventive control. Answer in writing: what is the difference between "the pipeline applied successfully" and "the infrastructure matches intent"?

**Pass criteria — all of the following must hold:**

- Every surgery step has a backup and an empty-plan acceptance check; imperative commands are justified or replaced by declarative blocks.
- The replacement design identifies the forcing attribute, the user impact and the technique that mitigates it.
- The pattern comparison names real costs (coupling, blast radius, wrong-workspace risk, extra system to operate).
- The drift design handles non-empty plans with an owner and separates role permissions (the plan role cannot change infrastructure).
- Failure-mode answers include detection, not only prevention, and the closing answer distinguishes apply success from intent.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-016 — Defend infrastructure lifecycle decisions** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-016).

Evidence to record: the state-surgery record, the comparison of change-control alternatives and the teardown evidence, plus every item under *Completion criteria* on that project step. Record **PRJ-016** as **Completed** in your progress record before opening the next module.
