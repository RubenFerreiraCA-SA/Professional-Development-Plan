# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-012**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-012](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-04-B — INFRASTRUCTURE AS CODE AND TERRAFORM — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Why infrastructure is described as code; providers, resources, data sources, state, plans, applies and modules; the `fmt` / `init` / `validate` / `plan` / `show` / `apply` workflow; reading plan symbols (`+`, `~`, `-`, `-/+`); and what to commit versus never commit (`.terraform.lock.hcl` versus state and secret variable files). Practice uses a local provider so no cloud account is needed.

**Out of scope:** Remote state and locking, environments, module design and testing, drift handling (`DEV-04-I`), CI plan/apply lanes and least-privilege automation (`DEV-04-P`), and state surgery or organisational strategy (`DEV-04-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Explain infrastructure as code and why it turns infrastructure changes into reviewable, repeatable pull requests rather than console clicks.
2. Define provider, resource, data source, state, plan, apply and module, and say which of them is a read-only lookup, which is a record of reality and which executes changes.
3. Run `terraform fmt -check`, `init`, `validate`, `plan -out`, `show` and `apply` on a small configuration using a local provider.
4. Read a plan: interpret `+`, `~`, `-` and `-/+`, and explain why a replacement can be harmless for a file and serious for a database or load balancer.
5. State that Terraform state is privileged data, list what to commit (`.tf`, `.terraform.lock.hcl`) and never commit (`*.tfstate`, `.terraform/`, secret variable files), and prepare the evidence for **PRJ-013**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-04-B — Infrastructure as Code and Terraform — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-dev-04-b)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-04` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Infrastructure as Code and Terraform — Beginner** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Write a configuration with a `local` provider, a variable, a `local_file` resource and an output. Run the full workflow and paste the plan and apply output.
2. Change the variable value and re-plan; then change the filename and re-plan. Explain the difference between an in-place update (`~`) and a replacement (`-/+`) in your own words.
3. Delete the managed file by hand and run `plan` again. Explain in one or two sentences why Terraform proposes to recreate it and what that tells you about state versus reality.
4. Run `terraform state list` and `terraform show`. Explain why state may contain sensitive values even when the configuration does not.
5. Write the `.gitignore` entries for a Terraform repository and say which Terraform-generated file you do commit and why.

**Pass criteria — all of the following must hold:**

- The workflow runs in the correct order and the plan is read before apply.
- The update/replacement explanation matches the plan symbols shown.
- The explanation of the deleted file connects configuration, state and real infrastructure.
- State is described as sensitive and access-controlled, not as a harmless cache.
- The `.gitignore` excludes state and `.terraform/`, and the lock file is committed to pin provider versions.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-013 — Describe infrastructure as configuration** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-013).

Evidence to record: the configuration, the plan output and a short explanation of resources, providers and state, plus every item under *Completion criteria* on that project step. Record **PRJ-013** as **Completed** in your progress record before opening the next module.
