# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **none — begin here**.

There are no preceding project steps for this first module, so the gate is satisfied from the start. Open the independent [Project Document](../../../4%20Project%20Document/Project.md) and note that your upcoming assignment is **PRJ-001**. From this point on, every later module enforces the rule below.

## MODULE DEV-01-B — REPOSITORY MANAGEMENT AND GIT — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Working tree, staging area (index), commits, branches, remotes and the pull-request workflow; first-repository hygiene (`.gitignore`, `.env.example`, README). You learn the vocabulary and the everyday loop (branch, edit, stage, commit, push, open a pull request) on a small practice repository.

**Out of scope:** Conflict resolution, history rewriting, repository governance (code owners, branch protection) and recovery techniques. These belong to `DEV-01-I`, `DEV-01-P` and `DEV-01-E`, and the step-by-step build of the Harbour repository belongs only in the Project Document.

### 2. Learning Objectives

1. Distinguish the working tree, the staging area (index), the local repository and a remote, and name the command that moves a change between each (`git add`, `git commit`, `git push`, `git fetch`).
2. Explain what a commit (a snapshot with an author, message and parent) and a branch (a movable pointer to a commit, not a copy of the project) really are.
3. Classify files as tracked, untracked or ignored, and write a `.gitignore` that excludes credentials, dependency/build output and Terraform state while committing a safe `.env.example` template.
4. Perform the everyday loop: create a purpose-named branch, stage selectively, commit with a clear message, push with upstream tracking and open a pull request whose description states purpose, scope, evidence and risk.
5. Explain why the hosting platform (reviews, branch rules, checks) is a different system from local Git, and prepare the evidence needed for **PRJ-001** (a repository with a useful README and a clean initial history).

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-01-B — Repository Management and Git — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-dev-01-b)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-01` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Repository Management and Git — Beginner** in your own words, without undocumented help, and keep the outputs with your progress record.

1. In a scratch directory run `git init -b main`, create a README and an `app/` directory containing a README, then paste the output of `git status` at three moments (files created, after `git add`, after `git commit`) with one sentence explaining what each output told you.
2. Create two branches that each change one different file, merge one into `main`, and paste `git log --oneline --graph --all` before and after. Explain in two sentences what a branch is and why no files were copied.
3. Scenario: you edited `README.md` and `config.yaml` but only `README.md` belongs in this commit. Write the exact commands to commit only the README and the command that proves what will be committed (`git diff --cached`).
4. Written answers: (a) What can the hosting platform enforce that local Git cannot see until a push is rejected? (b) Why does adding `.env` to `.gitignore` not protect a `.env` file that was already committed? (c) Give four patterns you would put in a `.gitignore` for a service that uses Docker and Terraform.

**Pass criteria — all of the following must hold:**

- Every command output matches the explanation given; tracked, untracked and ignored are used correctly.
- The branch explanation says a branch is a pointer, and the graph output shows the merged line of history.
- The selective commit uses `git add README.md` (or equivalent) and `git diff --cached` shows only the README.
- Answer (b) states that ignoring does not remove history and that a committed secret must be rotated; answer (c) includes `.env`, a dependency/build directory and `*.tfstate`/`.terraform/`.
- No credential or personal data appears in any submitted output.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-001 — Establish the training repository** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-001).

Evidence to record: the new repository URL, the README, the `.gitignore` and the initial commit hash, plus every item under *Completion criteria* on that project step. Record **PRJ-001** as **Completed** in your progress record before opening the next module.
