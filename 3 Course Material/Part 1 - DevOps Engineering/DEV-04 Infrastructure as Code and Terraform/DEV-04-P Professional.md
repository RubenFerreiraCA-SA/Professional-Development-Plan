# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-014**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-014](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-04-P — INFRASTRUCTURE AS CODE AND TERRAFORM — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Safe environment provisioning and change: the untrusted validation, trusted plan and trusted apply lanes with least-privilege federated identity; reviewer-facing plan summaries; re-planning in the apply context; state as a secret (encryption, versioning, restricted reads, restore path); module design rules (validated inputs, version pins, `moved` blocks, `prevent_destroy`); policy as code over plan JSON; cost, tags and teardown rehearsal; and blast-radius reasoning.

**Out of scope:** State surgery with import/`state mv`/`state rm`, provider and version governance, scheduled drift detection and multi-root/organisation strategy (`DEV-04-E`); basic workflows, remote state and modules (`DEV-04-B`, `DEV-04-I`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Separate three lanes: untrusted validation (`fmt`, `validate`, module tests, no credentials), trusted plan (federated identity with a plan-only role from allowed refs) and trusted apply (separate apply role behind environment approval), and explain why the same-repository pull request is not automatically trusted.
2. Publish a plan summary for reviewers (added, changed, destroyed, replaced, access widened) instead of the raw plan, always re-plan in the apply context, and apply the exact saved plan that was reviewed.
3. Protect state as a secret: encryption, versioning, restricted read access, `sensitive = true` understood as display-only, and a rehearsed recovery path (list object versions, restore with the lock held).
4. Apply module design rules: small modules, validated inputs, version pins and upgrade notes, `moved` blocks for renames, `lifecycle { prevent_destroy = true }` on stateful resources with a documented removal path, and policy-as-code checks (no public ingress, required tags, encryption, approved regions) over the plan JSON.
5. Control cost and blast radius: budget alarm and tags (`Project`, `Owner`, `Environment`), a written and rehearsed teardown order, and a plan review that names what will be replaced, what depends on it and what users will experience; prepare the evidence for **PRJ-015**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-04-P — Infrastructure as Code and Terraform — Professional](../../../5%20Textbook/Master%20Textbook.md#t-dev-04-p)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-04` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Infrastructure as Code and Terraform — Professional** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Draw or tabulate the three lanes with, for each, what runs, which identity it uses, which refs may trigger it and what state access it has. Identify the control that stops a malicious pull-request workflow from assuming the apply role.
2. Produce a reviewer-facing summary for a real plan JSON (`terraform show -json`): counts of create/update/delete/replace and any widening of access. Explain why you publish a summary and not the raw plan.
3. Write the state-protection design: backend encryption, versioning, who may read, the restore procedure, and why `sensitive = true` is not enough.
4. Demonstrate `moved` to rename a resource with an empty-of-replacement plan, `prevent_destroy` blocking a destroy, and a plan-JSON check (script or policy tool) that fails on a replacement of a protected resource or on open ingress.
5. Write a teardown order and cost note for your environment (including what dominates cost) and state what you would verify before approving a plan that replaces a load balancer.

**Pass criteria — all of the following must hold:**

- The lane design gives no credentials to untrusted code and uses distinct plan and apply identities.
- The summary lists replacements and access widening explicitly; apply uses a reviewed saved plan or an equivalent re-plan comparison.
- State protection covers encryption, versioning, restricted reads and restore, and treats state as production-secret material.
- The `moved`, `prevent_destroy` and policy-check demonstrations produce the expected plan or error output.
- The teardown order protects bootstrap resources, names cost drivers, and the review answer names dependants and user impact.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-015 — Demonstrate controlled infrastructure change** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-015).

Evidence to record: a reviewed plan summary, your state and locking approach and a recorded drift or failure investigation, plus every item under *Completion criteria* on that project step. Record **PRJ-015** as **Completed** in your progress record before opening the next module.
