# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-001](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-01-I — REPOSITORY MANAGEMENT AND GIT — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Git as a graph of snapshots (blobs, trees, commits, refs); working directory versus index versus `HEAD`; `restore`, `reset` and `revert`; merge base and two- versus three-dot diffs; merge, squash, rebase and cherry-pick; three-way conflicts; reflog recovery; `git bisect`; and a repeatable review workflow through pull requests.

**Out of scope:** Designing repository governance (code owners, branch protection, permission matrices), supply-chain controls and multi-team policy. Those belong to `DEV-01-P` and `DEV-01-E`; step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Describe commits as objects in a graph and inspect blobs, trees, commits and refs with `git cat-file -p`, `git ls-tree` and `git show-ref`, explaining why rewriting history changes commit identity.
2. Distinguish the working directory, the index and `HEAD` using `git diff`, `git diff --cached` and `git show`, and choose correctly between `restore`, `reset --soft/--mixed/--hard` and `revert` for a stated undo scenario.
3. Use `git merge-base`, `git log --graph --decorate --oneline --all` and two- versus three-dot diffs to explain how two branches diverged, and choose between merge commit, squash, rebase and cherry-pick for a given situation.
4. Resolve a three-way merge conflict by inspecting stages 1/2/3 (`git ls-files -u`, `git show :1:file`), preserving both sides' intent, running the tests before committing, and aborting safely with `git merge --abort`.
5. Recover a lost commit through the reflog, locate a regression with `git bisect run`, and prepare the evidence for **PRJ-002** (a branch, a deliberate change, a pull request and a review decision).

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-01-I — Repository Management and Git — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-dev-01-i)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-01` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Repository Management and Git — Intermediate** in your own words, without undocumented help, and keep the outputs with your progress record.

1. In a practice repository, make two clones, edit the same line of one file in both, push one and pull in the other. Show the conflict with `git status` and `git ls-files -u`, print stages 1, 2 and 3 of the file, and explain in your own words what each side intended.
2. Resolve that conflict so that both intentions survive, run a check (a test or a linter) and commit. Then demonstrate `git merge --abort` on a second, deliberate conflict and show the repository returned to its previous state.
3. Run `git reset --hard HEAD~1` on a disposable branch, find the lost commit with `git reflog`, restore it onto a `recovery` branch, and then use `git revert` to undo a different commit that you have already pushed. Explain why revert, not reset plus force-push, is correct for the pushed commit.
4. Given a 10-commit history with one test-breaking commit and a script that exits 0/1, find the offending commit with `git bisect run` and paste the transcript.
5. Choose merge commit, squash, rebase or cherry-pick for each of three scenarios you are given (tidy a private branch; backport a fix to a release branch; keep a large feature's context visible) and justify each in two sentences.

**Pass criteria — all of the following must hold:**

- Stage 1/2/3 output is shown and the explanation correctly identifies base, ours and theirs (and notes that ours/theirs swap during a rebase).
- The resolved file keeps both sides' behaviour, a check was run before the commit, and the abort demonstration leaves a clean `git status`.
- The lost commit is restored from the reflog onto a new branch without rewriting a shared ref, and the pushed commit is undone with `git revert`.
- The bisect transcript ends on the correct commit and ends with `git bisect reset`.
- Each integration choice names a concrete trade-off (history shape, backporting, traceability) rather than a preference.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-002 — Demonstrate collaboration and a reviewed change** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-002).

Evidence to record: the branch name, the pull request URL, the review comments and the final merge, plus the conflict-resolution commit, plus every item under *Completion criteria* on that project step. Record **PRJ-002** as **Completed** in your progress record before opening the next module.
