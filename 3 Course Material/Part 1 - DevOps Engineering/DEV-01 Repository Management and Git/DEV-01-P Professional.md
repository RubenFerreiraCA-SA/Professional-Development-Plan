# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-002**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-002](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-01-P — REPOSITORY MANAGEMENT AND GIT — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Repository governance and design: monorepo versus multi-repo versus a separate deployment-configuration repository; branching and history policy; ownership versus permission (CODEOWNERS, permission matrices, branch protection and rulesets); independent recovery of history incidents (reflog, revert, bisect, committed secrets); and the repository as a supply-chain boundary (secret scanning, scoped tokens, signed commits, required checks, workflow files as privileged code).

**Out of scope:** Critiquing governance at multi-team or organisational scale (bypass-actor audits, standards-as-code across many repositories, ownership rot) and advanced history tooling such as `worktree`, `rerere` and `range-diff`. Those belong to `DEV-01-E`; step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Design repository governance for a scenario: choose monorepo, multi-repo or a separate deployment-configuration repository using change frequency, ownership, secret boundaries and operational risk, and record the decision in an ADR with alternatives, consequences and a revisit trigger.
2. Define and document a branching and history policy (pull-request-only changes, squash versus merge-commit rules, tagged releases, no force-push to the default branch) and explain how it supports traceability, auditability and reproducible builds.
3. Model ownership versus permission: write a CODEOWNERS file and a permission matrix, and configure the branch protection or ruleset (required approvals, required status checks, code-owner review, blocked force-push and deletion) that makes ownership enforceable, naming common gaps such as administrator bypass and non-writable owners.
4. Recover from history incidents independently: restore unpublished work with `git reflog` and a recovery branch, undo published changes with a reviewed `git revert`, find regressions with `git bisect`, and respond to a committed secret by rotating it first and treating history rewriting as a coordinated last step.
5. Define the repository's supply-chain boundaries: state what each control (protected branch, code-owner review, secret scanning, scoped short-lived tokens, signed commits, required CI checks) reduces and does not prove, treat workflow files as privileged code, and prove enforcement with harmless failing attempts rather than screenshots of settings.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-01-P — Repository Management and Git — Professional](../../../5%20Textbook/Master%20Textbook.md#t-dev-01-p)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-01` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Repository Management and Git — Professional** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Governance design: for a fictional two-team service (application team and platform team, infrastructure changes need platform review) write an ADR choosing a repository model. It must compare at least two alternatives and state consequences and a revisit trigger.
2. Ownership: write a CODEOWNERS file covering `/app/`, `/infra/`, `/deploy/`, `/.github/` and `/docs/decisions/`, plus a permission matrix of roles against read, propose, approve, merge, change workflows and administer. Explain two ways a CODEOWNERS rule can exist yet fail to protect (for example the rule is requested but not required; the owning team lacks write access; administrators are exempt).
3. Enforcement evidence: list the branch rules you require on the default branch, then describe three harmless tests that would prove enforcement (direct push rejected, `infra/` change without owner approval blocked, administrator bypass checked) and the output each test should produce. If the platform plan cannot enforce a rule, write "not enforceable here" and name the compensating control.
4. Recovery: on a disposable branch, lose three commits with a hard reset and restore them via the reflog; undo a pushed change with `git revert`; and state the exact first three actions you would take if an API token were found in a pushed commit.
5. Threat reasoning: an external contributor edits a workflow file that runs with a publishing token. Answer the five questions (what triggers automation, what permissions untrusted code receives, which refs can publish, who can change workflow files and approve that change, how a suspicious change would be detected and revoked).

**Pass criteria — all of the following must hold:**

- The ADR uses explicit criteria (change frequency, ownership, secrets, tooling, risk), not preference, and names at least one rejected alternative with a reason.
- CODEOWNERS paths match the matrix; the two failure examples are accurate; ownership is not confused with permission.
- Every enforcement test has an expected observable result (a rejected push message, a blocked merge), and unenforceable controls have a stated compensating control.
- The reflog recovery restores all three commits; revert is used for the published change; the secret response begins with revocation or rotation, not history deletion.
- The threat answers identify that workflow files are privileged code and name an ownership or approval control for them.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-003 — Apply governance and recover a mistake** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-003).

Evidence to record: your ownership and protected-change rules, an enforcement test showing a rejected change, and the disposable-branch recovery transcript, plus every item under *Completion criteria* on that project step. Record **PRJ-003** as **Completed** in your progress record before opening the next module.
