# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-003**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-003](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-01-E — REPOSITORY MANAGEMENT AND GIT — EXPERT

### 1. Topic and Scope

**In scope for this level:** Critiquing branching and integration strategy at scale (squash versus merge versus rebase versus cherry-pick, reverting merges, tracking backports); advanced history techniques and their operational risks (`worktree`, `rerere`, `range-diff`, sparse checkout and partial clone, submodules versus monorepo, signed commits); governance failure modes (bypass actors, workflow files as privileged code, review theatre, ownership rot, history rewriting under pressure); standards-as-code across many repositories; and end-to-end traceability from running artifact to reviewed change.

**Out of scope:** Introductory vocabulary, conflict resolution mechanics and the construction of a single repository's governance (`DEV-01-B`, `DEV-01-I`, `DEV-01-P`), and implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Compare merge commit, squash, rebase and cherry-pick at scale on bisect granularity, revertibility (including `git revert -m 1` of a merge and reverting the revert before re-merging) and backport tracking (`git cherry-pick -x`, labels, release branches).
2. Evaluate advanced techniques (`git worktree`, `git rerere`, `git range-diff`, sparse checkout and partial clone, submodules versus monorepo, signed commits) by the problem each solves and the operational risk each introduces.
3. Diagnose governance failure modes (bypass actors, workflow files as privileged code, review theatre, ownership rot, history rewriting under pressure) and propose measurable mitigations such as bypass audits, CODEOWNERS linting and review-size limits.
4. Design repository standards for many repositories as code (hosting API or Terraform provider), including required checks, secret scanning and templates, and detect drift from the standard instead of configuring each repository by hand.
5. Argue end-to-end traceability: from a running artifact, show which commit built it, who reviewed it, which workflow run produced it and which approvals gated it; identify the weakest link and test which controls still hold if a maintainer account is compromised.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-01-E — Repository Management and Git — Expert](../../../5%20Textbook/Master%20Textbook.md#t-dev-01-e)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-01` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Repository Management and Git — Expert** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Run an experiment: integrate the same four-commit feature branch into three copies of `main` using merge commit, squash and rebase-then-fast-forward. For each, show the resulting graph, the commit count available to `git bisect`, and the command and result of reverting the whole feature. Include `git revert -m 1` for the merge-commit case and what happens when you re-merge the same branch afterwards.
2. Backport design: cherry-pick one fix onto `release/1.0` with `-x`, show the trailer, then merge `main` into `release/1.0` and explain the risk of duplicate or conflicting application. State how your team would track backports.
3. Write a one-page critique of a governance model (given or your own) identifying at least three failure modes from the list above, the evidence you would collect to confirm each (for example the list of bypass actors, review latency, stale CODEOWNERS entries) and a mitigation for each.
4. Traceability walk: for a built artifact, document the chain digest → commit → pull request → reviewers → workflow run → approvals, mark each link as enforced, recorded-only or asserted, and name the weakest link.
5. Mentoring prompts, answered in writing: Why can `git reset --hard` plus force-push be legitimate on a private branch and a policy violation on `main`? What evidence would convince you that a code-owner rule binds administrators? Which of your controls survive a compromised maintainer account?

**Pass criteria — all of the following must hold:**

- The experiment shows measurably different histories and bisect resolution for the three strategies, and the merge revert uses `-m 1` correctly.
- The backport description explains that cherry-picks create new commit identities and gives a concrete tracking mechanism.
- Each failure mode is paired with observable evidence and a measurable mitigation, not a general instruction to be careful.
- Every link in the traceability chain is classified honestly; asserted links are not presented as enforced.
- The mentoring answers distinguish private from shared refs, ask for enforcement evidence (a rejected action), and name controls that do not depend on a single account.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-004 — Defend and improve the repository workflow** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-004).

Evidence to record: the strategy comparison, the backport record, the governance critique and the traceability walk, summarised in an ADR, plus every item under *Completion criteria* on that project step. Record **PRJ-004** as **Completed** in your progress record before opening the next module.
