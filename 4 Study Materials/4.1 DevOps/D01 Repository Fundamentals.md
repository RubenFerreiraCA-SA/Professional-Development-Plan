# Chapter 1 — Repository Fundamentals (D01)
*DevOps Engineering textbook · Chapter 1 of 8*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [D01 course detail](../../3%20Course%20Detail/3.1%20DevOps/D01%20Repository%20Fundamentals.md) for the current planning estimate. |
| **Prerequisites** | Comfort with a command line, writing software, Git commits and using a remote Git repository. No prior repository governance experience required. |

## How to use this textbook

**Work through each section in order.** Every section adds something to the *same* running project. At the end you will have a small repository that an application team and a platform team can use safely. The explanations begin with fundamentals, but the decisions and final assessment are intended for experienced software developers.

Each section contains: **Concept → Worked example → Practice → Verify → Reflect.** Commands target a POSIX shell (Linux/macOS or an equivalent terminal). Use GitHub or GitLab where a hosted provider is needed; controls differ by provider and account plan.

**The relationship to the programme:** [D00 syllabus](../../3%20Course%20Detail/3.1%20DevOps/D00%20DevOps%20Syllabus.md) describes the pathway; [D01 course detail](../../3%20Course%20Detail/3.1%20DevOps/D01%20Repository%20Fundamentals.md) defines the outcomes and assessment requirements. This book *teaches* those requirements. The project can grow into the [programme Final Project](../../1%20Foundational%20Documents/1.4%20Final%20Project.md).

> **Safety boundary:** Use a disposable or personally controlled training repository. Never copy real secrets, confidential employer code or production credentials into it. Later exercises discuss security failures using fabricated data only.

## Your running project: a small delivery platform

You are building the repository foundation for a fictional service called **Harbour API**. An application team owns the API; a platform team owns infrastructure and deployment configuration. The eventual platform will build, deploy and monitor the service, but those capabilities arrive in later modules.

At the beginning, all you need is Git and a terminal. By the end, the same repository will contain these responsibilities:

| Path | Responsibility | Intended owner |
| --- | --- | --- |
| `app/` | Application source and tests | Application team |
| `infra/` | Infrastructure definitions, added later in D05 | Platform team |
| `deploy/` | Deployment declarations, added later in D06 | Platform team |
| `docs/decisions/` | Short architecture decision records (ADRs) | Appropriate reviewers |
| `.github/` or GitLab configuration | Repository-specific automation, governance | Repository maintainers |

Do not confuse directories with actual isolation: moving a file under `infra/` does **not** restrict who can edit it. Repository permissions and review enforcement are separate concerns.

---

## Section 1.1 — Why repositories need architecture

### 1.1.1 From storage to an engineering interface

A repository stores tracked files and their history, but an engineering organisation also uses it to define *how work moves toward production*. A newcomer should be able to answer:

- Where does application code belong?
- Who is responsible for reviewing an infrastructure change?
- What must happen before a change can enter the default branch?
- Which files must never be committed?
- How can a deployment artifact be traced back to reviewed source?

A repository that answers these questions consistently is a **developer interface**. This is one of Platform Engineering's goals: make the safe path understandable and repeatable.

**Worked example.** Suppose a developer changes the API's timeout. If application code and production infrastructure share a repository with no ownership rules, that developer may unintentionally change deployment configuration in the same pull request. A thoughtful directory structure makes the boundary visible; review rules and automated checks later enforce it.

### 1.1.2 Repository models and their trade-offs

A **monorepo** houses multiple related components together. It simplifies coordinated changes and shared visibility, but can increase permission complexity and pipeline cost.

A **multi-repository** approach separates components. Teams can have different release and access policies, but cross-repository version coordination becomes harder.

A **separate deployment-configuration repository** can isolate production desired state from application development. It provides a clear GitOps approval boundary, but creates a promotion step and more repositories to maintain.

There is no universally correct model. Choose based on change frequency, ownership, secrets boundaries, build tooling and operational risk—not fashionable terminology.

### 1.1.3 Create the project

Run the following in an empty training directory (replace the name if it already exists):

```bash
mkdir harbour-platform
cd harbour-platform
git init -b main
mkdir -p app infra deploy docs/decisions
printf '# Harbour Platform\n\nTraining repository for a reusable delivery platform.\n' > README.md
printf '# Contributing\n\nAll changes to main should be proposed through a pull request.\n' > CONTRIBUTING.md
printf 'Harbour API source code will be added during D03.\n' > app/README.md
printf 'Terraform infrastructure will be introduced in D05.\n' > infra/README.md
printf 'Deployment configuration will be introduced in D06.\n' > deploy/README.md
git status
```

**What happened?** `git init -b main` created a local repository with `main` as its initial branch. `mkdir -p` created folders. The README files are deliberate: Git tracks files, not empty folders. `git status` shows the new files as untracked until you stage them.

```bash
git add README.md CONTRIBUTING.md app/README.md infra/README.md deploy/README.md
git commit -m "chore: establish repository boundaries"
git log -1 --oneline
```

**Expected observation:** Git reports a commit on `main`; the files are no longer untracked. If Git asks for an author identity, configure it for the training repository with `git config user.name` and `git config user.email`, then repeat the commit. Your author identity is not the same as repository authentication.

**Practice 1:** Add `docs/architecture.md` explaining which team owns each directory. Add a separate `tests/` directory only if you can explain why its tests should not live beside the application. Commit the change.

**Verify:** A new engineer should be able to inspect the top-level README, navigate to each component and understand the intended boundaries without asking you.

**Reflect:** If app and infrastructure are reviewed by different groups, is a single repository still acceptable? What extra controls would make it so?

---

## Section 1.2 — Collaboration: remotes, branches and reviewed changes

### 1.2.1 Local Git and the remote host are different systems

Git maintains local history. GitHub or GitLab hosts a copy and adds collaboration features: pull/merge requests, permissions, code reviews, checks and branch rules.

A **remote** is a named destination for fetching and pushing Git refs. A **branch** is a movable reference to a commit. A **pull request** (GitHub) or **merge request** (GitLab) is a *hosting-platform review workflow*, not a special Git object.

These distinctions matter when a review seems approved but the actual commit changes, or when a remote policy differs from what local Git allows.

### 1.2.2 Connect the training repository

Create an **empty repository** in your chosen Git host, without automatically generating an additional README. Choose private visibility if practical. Copy its HTTPS or SSH clone URL.

```bash
git remote add origin <YOUR-REPOSITORY-URL>
git remote -v
git push -u origin main
```

Here `origin` is just a conventional remote name. The `-u` establishes upstream tracking, making later `git push` and `git pull` operations more convenient.

**Authentication options:** HTTPS typically uses a credential helper and an appropriately scoped token; SSH uses a key registered with the host. Prefer the organisation's approved authentication method, use MFA for the account, and never store tokens in the repository or paste them into a committed script.

**Troubleshooting:** A 403/permission error may mean wrong credentials or insufficient repository rights. A non-fast-forward error means the remote history advanced. Inspect and integrate carefully; do not reflexively force-push to `main`.

### 1.2.3 Work through a branch

```bash
git switch -c docs/add-onboarding
cat >> CONTRIBUTING.md <<'EOF'

## Getting started
1. Read README.md and the relevant component README.
2. Create a branch for the change.
3. Run the relevant checks before requesting review.
4. Explain risks and link supporting evidence.
EOF
git add CONTRIBUTING.md
git commit -m "docs: explain onboarding"
git push -u origin docs/add-onboarding
```

Open a pull/merge request in the host UI from `docs/add-onboarding` to `main`.

A useful request explains the *purpose*, *scope*, *test or validation evidence*, *risk* and *reviewers*. A reviewer should understand why the change is safe without reading your mind.

**Example request description:**

```text
Purpose: Make onboarding reproducible for new engineers.
Changes: Add a four-step contribution workflow.
Validation: Read each instruction from a fresh clone.
Risk: Documentation only; no runtime changes.
```

Request review where possible. If you are the only contributor, use a second authorised reviewer when available or document that independent approval cannot be demonstrated.

**Practice 2:** Create another branch that changes `infra/README.md`. In the request description explain why this apparently simple change should be examined by the platform owner.

**Verify:** Inspect the remote's pull/merge request view. Can you identify the source branch, target branch, changed files, commits, approvals and merge result? Are approval *requirements* actually enforced or merely requested?

**Reflect:** Why is a reviewed request preferable to sending a patch through chat? What would still be missing if the reviewer never ran any tests?

---

## Section 1.3 — Repository hygiene and the boundary around secrets

### 1.3.1 Tracked, untracked and ignored are different states

Git records files once you stage and commit them. A `.gitignore` file prevents *untracked* matching files from being suggested for addition in ordinary workflows. It does **not** remove tracked content from history and does **not** secure a secret.

Working example: a Terraform state file can contain credential-like values even when its configuration file contains no obvious passwords. A local `.env` file often holds development credentials. Neither belongs in a public training repository.

Create a root ignore file:

```gitignore
# Local configuration and credentials
.env
.env.*
!.env.example
*.pem
*.key

# Build and dependency outputs
node_modules/
dist/
coverage/

# Terraform local and state files
.terraform/
*.tfstate
*.tfstate.*
*.tfplan
crash.log

# Editor and OS noise
.DS_Store
```

Store that content in `.gitignore`. Note that `.terraform.lock.hcl` is intentionally **not** ignored: it is commonly committed to help control provider selections.

Run:

```bash
printf 'TRAINING_ONLY=not-a-real-secret\n' > .env
printf 'TRAINING_ONLY=replace-me\n' > .env.example
git check-ignore -v .env
git check-ignore -v .env.example || true
git status --short
```

**Expected:** `.env` is ignored; `.env.example` can be tracked. The `|| true` lets the check continue when the file is correctly *not* ignored (exit status 1). Review the output rather than treating command success alone as proof.

### 1.3.2 What if a secret was already committed?

If a real credential enters Git history, **revoke or rotate it first**. Removing the current file is insufficient: clones, caches and earlier commits may retain it. History rewriting is a separate, carefully coordinated response with significant disruption and is covered only at a conceptual level here; advanced history mechanics belong in D02.

Use a fabricated token string to demonstrate a preventative scanner. Choose an approved scanner supported by your host or development environment, and explain its false-positive and false-negative limitations. Never create a real credential for the exercise.

**Practice 3:** Write a short `docs/security.md` that identifies likely sensitive file types, the location of *approved* secrets at build and runtime (high-level only), and the response to accidental exposure.

**Verify:** `git ls-files` does not list `.env` or state files. `git check-ignore -v` explains which ignore rule matches. Explain why this is not evidence that secrets have never been committed historically.

**Reflect:** Why should a dependency lockfile normally be committed while a local dependency installation directory is ignored?

---

## Section 1.4 — Ownership is not the same as permission

### 1.4.1 Identify who is accountable

A code owner is the person or team responsible for reviewing changes in a particular part of the codebase. **Ownership is a review and accountability concept**; filesystem layout alone does not enforce it.

A protected branch is a host-side policy controlling what changes may reach a branch. Common options include requiring pull/merge requests, reviews, status checks, signed commits or restrictions on force-push and deletion.

A repository role governs what an identity can do (read, write, maintain, administer). A permission and an approval rule solve different problems: someone may be allowed to propose an infrastructure change without being allowed to approve or merge it.

### 1.4.2 Worked example: GitHub CODEOWNERS

If using GitHub, create `.github/CODEOWNERS`:

```text
/app/       @YOUR-ORG/app-maintainers
/infra/     @YOUR-ORG/platform-maintainers
/deploy/    @YOUR-ORG/platform-maintainers
```

Replace the placeholders with **existing users or teams that have appropriate repository access**. This syntax is illustrative; a nonexistent team will not become an enforced reviewer. On GitLab use the provider's CODEOWNERS syntax and approval configuration.

**Important nuance:** In GitHub, the CODEOWNERS file identifies requested owners, but a branch protection rule or ruleset requiring code-owner review is needed to *enforce* that review. Host plans and repository settings may restrict what you can enable.

### 1.4.3 Build a permission matrix

Write down the intended rules **before** clicking settings:

| Identity | Read source | Propose change | Approve app change | Approve infrastructure change | Administer rules |
| --- | --- | --- | --- | --- | --- |
| Application developer | Yes | Yes | If authorised | Not by default | No |
| Platform maintainer | Yes | Yes | If authorised | Yes | Not necessarily |
| Repository administrator | Yes | Yes | Depends on policy | Depends on policy | Yes |
| CI validation identity | Yes, minimal | No by default | No | No | No |

This is a *design example*, not an automatically implemented access policy. Your host may not support every combination in one repository. If per-directory write restrictions are required rather than review approval, evaluate separate repositories or additional policy tooling.

**Practice 4:** In your training repository, configure `main` to disallow force-push/deletion and require a reviewed pull/merge request where supported. Enable code-owner approval for sensitive paths when the provider permits it.

**Verify:** Try to push a harmless direct change to `main` from an authorised test identity **without force-pushing**. If rejected, record the policy result. If accepted, document the configuration or plan limitation and do not claim the branch was protected.

**Reflect:** Can an administrator bypass these rules? What controls make exceptions visible and accountable?

---

## Section 1.5 — The repository as a software supply-chain boundary

### 1.5.1 Why trust must follow the change

Consider this chain:

```text
Developer identity
    → reviewed source change
    → automated checks
    → build identity
    → released artifact
    → deployment environment
```

D01 establishes the **first** boundary. Later modules build the pipeline (D04), infrastructure (D05) and deployment controls (D06).

Threats include a stolen developer credential, an untrusted pull request that executes hostile code, a leaked CI token, an unreviewed dependency update and an unauthorised change to deployment definitions.

Protecting `main` is essential but not sufficient. A passing review does not prove a package is safe, a commit signature does not guarantee correct code, and repository access does not establish who deployed an artifact.

### 1.5.2 Design controls according to their purpose

| Control | Protects against | Does **not** guarantee |
| --- | --- | --- |
| MFA on user accounts | Some account takeover routes | The account cannot be compromised |
| Protected default branch | Unreviewed or destructive changes under an enforced rule | Every merged change is secure |
| Code-owner reviews | Changes bypassing the required domain review | Reviewers cannot make mistakes |
| Secret scanning | Recognised credential patterns entering source | Every secret is identified |
| Scoped tokens | Excessive consequences of token compromise | Malicious code cannot misuse allowed permissions |
| Signed commits/tags | Some forms of provenance spoofing | The signed content is trustworthy |
| Required CI checks | Merging without specified validations | The test suite covers all risks |

### 1.5.3 Worked threat scenario

Imagine an external contributor opens a request that modifies `.github/workflows/release.yml`. A workflow running untrusted source with a token capable of publishing packages may leak or misuse credentials. That can happen even though the application code looks harmless.

Record these questions in `docs/security.md`:

1. Which repository events trigger validation?
2. What permissions does untrusted code receive?
3. Which branches or environments can publish artifacts?
4. Who can change workflow definitions and approve those changes?
5. How will a suspicious change be detected, revoked and investigated?

You are **not** required to implement CI here; this is the threat model that D04 will later turn into tested controls.

**Practice 5:** Write a small trust-boundary diagram for your repository and identify at least three attacker or mistake scenarios. For each, propose one preventive control and one way to verify it.

**Verify:** Your document distinguishes *a configured setting*, *an enforced restriction* and *a recommendation not yet implemented*.

---

## Section 1.6 — Document decisions instead of accumulating rules

### 1.6.1 The architecture decision record

Engineers need to know not only **what** was chosen, but **why**. An ADR makes important trade-offs discoverable after the original author leaves.

Create `docs/decisions/0001-repository-strategy.md`:

```markdown
# ADR 0001 — Repository strategy

Status: Accepted
Context: Application and platform teams need coordinated changes,
but infrastructure changes require separate review.

Decision: Start with one repository containing app/, infra/ and deploy/.
Require code-owner reviews for infra/ and deploy/ where enforceable.

Alternatives:
- Separate app and infrastructure repositories.
- Separate GitOps desired-state repository.

Consequences:
- Easier coordinated development and shared history.
- Stronger reliance on host permissions and review policies.
- Reconsider repository split if production access boundaries demand it.
```

The file above is a **starting point**, not a conclusion you must copy. Make an actual decision based on your scenario. A useful ADR is short enough to read and specific enough to disagree with.

### 1.6.2 Make onboarding a repeatable contract

Expand `CONTRIBUTING.md` to answer:

- How to obtain the repository and required development tools.
- Where each category of change belongs.
- How to name branches and explain a proposed change.
- What validation a contributor must run or supply.
- When to request application versus platform review.
- How to report suspected credential exposure.
- Where to find decisions and operating limitations.

**Practice 6:** Ask someone else to read the guide, or deliberately follow it from a fresh clone in a separate directory. Record every missing instruction. Revise the document based on that evidence.

**Verify:** A new contributor can propose a harmless documentation change without private instructions from the repository author.

**Reflect:** What should be standardised across *all* platform-managed repositories? What should remain an application-team choice?

---

## Section 1.7 — Put the repository under test

The earlier chapters produced a repository layout, a collaboration workflow, ignore rules, ownership intentions, provider controls and an ADR. Now test them together.

### 1.7.1 Integration exercise

Create a feature branch that changes two things: an application README and an infrastructure README. Open a pull/merge request and observe which reviewers are requested. Explain whether the merge is blocked until an authorised reviewer approves it.

Then create a second harmless request that affects only `app/`. Compare the review requirements. If your host cannot enforce the distinction, explain the limitation and what repository architecture or host policy could solve it.

### 1.7.2 Test the failure modes

Use a training identity and non-sensitive changes:

1. Attempt a direct push to protected `main`; record rejection or limitation.
2. Check that `.env` and Terraform state files are ignored *before* they are ever staged.
3. Attempt to submit a change in `infra/` without the intended reviewer; record the actual merge gate.
4. Check that an administrator or bypass identity is not silently exempt from the control you rely on (or document why testing that role is unavailable).
5. Inspect the repository's commit and review history. Can you connect an accepted change with its author, reviewers and reason?

Do not create real secrets, destructive branch mutations or intentionally malicious workflows to perform these tests.

### 1.7.3 The difference between evidence and assertion

A screenshot of a branch-rule setting proves it was displayed. A rejected unauthorised merge attempt offers stronger evidence that it was *enforced*. Conversely, a plan limitation means you cannot demonstrate enforcement. In a professional assessment, saying **“not enforceable in this environment; here is the alternative”** is better than pretending.

---

## Practical Assessment — Chapter 1 — production-ready repository foundation

**Scenario:** You are joining a platform team supporting two delivery groups. Developers need a straightforward contribution process. The application team should be able to work rapidly, while production-related infrastructure and deployment changes demand stronger oversight.

**Your task:** Deliver an auditable, understandable repository that another engineer can safely contribute to.

### Required deliverables

1. **Working repository:** `app/`, `infra/`, `deploy/`, `README.md`, `CONTRIBUTING.md`, secure ignore rules and an appropriate ownership file.
2. **Architecture decision:** A real ADR comparing one repository against at least one split-repository option, including permissions, change coupling and operational cost.
3. **Governance model:** Explicit role/permission matrix, main-branch settings, code-owner policy and rationale for restrictions.
4. **Reviewed change:** A pull/merge request demonstrating the intended process, with validation notes and reviewer evidence where available.
5. **Security model:** A brief threat analysis covering credentials, untrusted changes and the boundary between code review and trusted release automation.
6. **Failure evidence:** A harmless direct-push test, an ignored-secret-file test and an infrastructure-review test, recording what actually happened.
7. **Onboarding test:** A fresh-clone walkthrough (or second-author walkthrough) that identifies and resolves at least one documentation ambiguity.

### Evaluation rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Architecture | Folders exist but rationale is unclear | Ownership and repository choices are justified | Trade-offs include future scaling and trust boundaries |
| Collaboration | Contributions depend on tribal knowledge | A new developer can follow the guide and propose a reviewed change | Workflow minimises friction while making exceptions auditable |
| Governance | Rules are documented but untested | Enforcement is demonstrated, or limitations are stated accurately | Alternative policies and bypass risks are explicitly evaluated |
| Security | Generic list of security advice | Secrets and permissions have a specific threat model and controls | Controls are prioritised by attacker capability and blast radius |
| Evidence | Screenshots or assertions only | Reproducible tests and clear results | Another engineer independently validates the key controls |

**Completion standard:** Meet the **Competent** description across all five dimensions. If a hosting feature is unavailable, show that you understand its purpose and provide a defensible, documented alternative. The goal is engineering judgement and a usable developer experience, not a perfect score or a feature-rich GitHub plan.

### Model answer outline (for self-review)

An acceptable submission might choose a monorepo because coordinated application and infrastructure changes are common, but protect `main`, require reviews for `infra/` and `deploy/`, define eligible code owners and explicitly document any hosting-plan enforcement gap. It would show a successful reviewed documentation change, a rejected unauthorised change *when supported*, a verified ignore rule, and an ADR stating when a separate desired-state repository would be preferable.

There is no single correct repository layout. There **must** be a clear relationship between architecture, controls, verification and the needs of other developers.

## Glossary

| Term | Meaning |
| --- | --- |
| Repository | Versioned collection of source files and Git history |
| Remote | Named destination for fetching/pushing Git refs |
| Default branch | Main integration branch used by the repository |
| Pull/merge request | Host-provided review and integration workflow |
| Code owner | Team or person responsible for reviewing changes in a scope |
| Protected branch | Hosted rule limiting changes to a named branch |
| Least privilege | Giving identities only the permissions needed for their responsibilities |
| Supply chain | Sequence of identities, dependencies, processes and artifacts leading from source to deployed software |
| ADR | Short record of an architectural decision and its consequences |

## Further reading

Use these as references when a feature behaves differently on your host—not as a substitute for the chapters:

- [Pro Git — Getting Started](https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control)
- [Git — gitignore](https://git-scm.com/docs/gitignore)
- [GitHub — Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub — CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitLab — Protected branches](https://docs.gitlab.com/user/project/repository/branches/protected/)

**Course detail:** [D01 — Repository Fundamentals](../../3%20Course%20Detail/3.1%20DevOps/D01%20Repository%20Fundamentals.md) · **Next chapter:** [Chapter 2 — Advanced Git](D02%20Advanced%20Git.md)
