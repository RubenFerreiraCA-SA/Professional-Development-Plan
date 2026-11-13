# D01 — Git & Repository Foundations

**Level:** Upper-intermediate to senior software developers  
**Estimated study time:** 8–10 hours  
**DevOps syllabus weighting:** 7%  
**Prerequisites:** Confident daily use of Git, branching, commits, pull/merge requests and command-line tools.

## Objective

**Design, secure and operate a repository workflow suitable for a production engineering team.** Go beyond basic commands to understand Git's object model, maintain a trustworthy history, recover from failures and enforce review and release controls without making delivery unnecessarily difficult.

The resulting repository becomes the foundation for the [DevOps capstone](DevOps_Syllabus.md). This module deepens the D01 syllabus objectives; it does not replace them.

## Outcomes

After completing the module, you should be able to:

1. Interpret Git's commit graph, object references and three-tree model to diagnose unexpected repository states.
2. Choose and defend a branching, merging and history policy appropriate for continuous delivery and a multi-developer team.
3. Resolve non-trivial conflicts, recover lost or incorrect work and safely investigate regressions.
4. Design a repository layout that separates application, infrastructure and deployment concerns while defining clear ownership boundaries.
5. Implement enforceable repository governance: least-privilege access, protected branches, approval rules, ownership and automated policy checks.
6. Identify and mitigate source-control supply-chain risks, including exposed secrets, untrusted automation and unauthorised changes.
7. Demonstrate the workflow and its failure modes with reproducible evidence.

## Time budget

| Activity | Estimated hours |
| --- | ---: |
| Git internals and history engineering | 2 |
| Conflict resolution, recovery and debugging | 2 |
| Repository architecture and ownership | 1.5 |
| Governance, identity and supply-chain controls | 2 |
| Integrated scenario, validation and technical decisions | 1.5–2.5 |
| **Total** | **9–10** |

Use an isolated repository for destructive experiments. Advanced extensions are optional and sit outside the estimated core hours.

## 1. Git internals and history engineering

**Concepts:** blobs, trees, commits, annotated tags, refs, `HEAD`, the index, detached HEAD, unreachable objects, reflogs and the difference between author and committer metadata.

Explain how the following operations alter the commit graph, and why a team might choose one over another:

- **Merge commit:** preserves the topology and branch context.
- **Squash merge:** gives a linear mainline but discards individual feature commits on that branch's merged result.
- **Rebase:** replays commits with new identities; useful before integration, risky when rewriting others' shared history.
- **Cherry-pick:** replays selected changes, useful for controlled backports but introduces duplicate commit identities.

**Inspect a real repository:**

```bash
git log --graph --decorate --oneline --all
git cat-file -t HEAD
git cat-file -p HEAD
git ls-tree -r --name-only HEAD
git reflog --date=iso
git merge-base main feature/example
git diff main...feature/example
```

Use an existing branch in place of `feature/example`. Explain why the three-dot comparison is appropriate for reviewing changes since a common ancestor, and how it differs from comparing two endpoints.

**Exercise:** In a disposable repository, create two branches with divergent commits. Merge one using a merge commit and the other using a squash merge. Compare `git log --graph`, the resulting file trees and traceability. Write a short decision on which policy you would adopt and why.

## 2. Conflict resolution, recovery and regression diagnosis

**Scenario A — concurrent development:** Use **two clones** of a disposable repository to model developers changing the same line. Fetch and integrate the competing change, inspect the conflict stages and resolve it deliberately:

```bash
git fetch origin
git status
git ls-files -u
git diff --cc
# Resolve conflicted files, run appropriate checks, then:
git add <resolved-file>
git rebase --continue
```

The continuation command applies **only if you chose rebase**. For a merge conflict, complete the merge using `git commit` or `git merge --continue`. Explain when aborting (`git rebase --abort` or `git merge --abort`) is preferable.

**Scenario B — lost work:** In a disposable branch, create a commit, record its hash, then move the branch backwards. Use `git reflog` to find and restore the commit on a **new recovery branch**. Do not reset or rewrite the shared `main` branch. Compare:

- `git revert` for undoing a published change without rewriting public history.
- `git reset` for moving local refs and, optionally, changing index and working-tree state.
- `git restore` for recovering selected file content.
- `git reflog` for finding previously referenced commits; recovery depends on retention and garbage collection.

**Scenario C — regression:** Deliberately introduce a failing change among several good commits. Use `git bisect start`, `git bisect good` and `git bisect bad` with an existing test or reproducible manual check to identify the first bad commit. Finish with `git bisect reset`.

**Deliverable:** A brief incident note showing the divergent graph, conflict resolution, recovered commit and regression culprit. Explain the safe recovery option you would use for a production branch.

## 3. Repository architecture and code ownership

Create or refactor the ongoing capstone repository:

```text
capstone/
├── app/                   # Application code and tests
├── infra/                 # Infrastructure as code
├── deploy/                # Deployment and GitOps configuration
├── docs/
│   └── decisions/         # Architecture decision records
├── .github/ or .gitlab/   # Hosting-specific automation/configuration
├── .gitignore
├── README.md
└── CONTRIBUTING.md
```

Keep the structure intentionally small; avoid creating empty directories without a reason. The same architecture can be implemented on GitHub or GitLab, with platform-specific controls clearly documented.

**Design exercise:** Decide whether the project should remain a monorepo, split into application/infrastructure repositories, or evolve into a separate deployment-config repository. Evaluate change coupling, permissions, ownership, release cadence, auditability and GitOps reconciliation. Record the decision in a one-page ADR with alternatives and trade-offs.

Define code ownership at least for `app/`, `infra/` and `deploy/`. On GitHub, an example `.github/CODEOWNERS` is:

```text
/app/       @your-org/app-maintainers
/infra/     @your-org/platform-maintainers
/deploy/    @your-org/platform-maintainers
```

Replace placeholders with real, eligible teams. A CODEOWNERS file alone does **not** enforce approvals; combine it with review rules and verify that the required reviewers can actually access the repository. For GitLab, use its supported code-owner syntax and approval settings.

**Repository hygiene:** Implement a suitable `.gitignore` for your chosen stack, excluding local secrets, build products and Terraform state while retaining intentional dependency lockfiles. Demonstrate `git check-ignore -v` and `git ls-files`. Discuss the limitations of `.gitignore` once a secret is already tracked.

## 4. Governance, identity and software supply-chain security

Treat the repository as a **security boundary**, not merely a storage location.

| Control | Design question / evidence |
| --- | --- |
| Permissions | Who may read, push, approve, administer and publish? Are service accounts scoped narrowly? |
| Protected default branch | Are direct pushes, force pushes and deletion restricted? Are bypasses audited or limited? |
| Reviews | Are independent approvals and code-owner reviews required for sensitive paths? |
| Automated checks | Which tests, scans and policies must pass before merge? D03 will build the actual CI pipeline. |
| Identity and provenance | Which authentication methods, MFA policies and commit/tag signing options are available? |
| Secrets | How are tokens issued, stored, rotated and prevented from entering history? |
| Dependencies and automation | Can untrusted pull requests access credentials? Are actions/runners/dependencies reviewed and pinned where appropriate? |
| Releases | How are tags protected and how can the team trace an artifact back to reviewed source? |

**Implement and demonstrate**, where supported by your hosting plan and permissions:

1. Protect `main`, disable force-pushing and deletion, and require changes through pull/merge requests.
2. Configure an approval rule and code-owner review for sensitive paths. Where a solo or private-repo plan cannot enforce this, document the gap rather than claiming it works.
3. Use a feature branch to propose a change in `infra/` or `deploy/`; capture the review and merge record.
4. Verify that an unauthorised direct update is rejected or document why enforcement cannot be tested.
5. Add a lightweight secret-detection safeguard, such as an approved local pre-commit scanner or repository-native secret scanning. **Use fabricated test strings only**; never plant real credentials for the exercise.

Review SSH keys, scoped tokens and signed commits/tags as options rather than mandatory setup steps. A valid signature proves possession of a key, not that the change is safe. Understand how compromised credentials, unsafe workflow triggers and excessive CI token permissions can undermine an otherwise protected repository.

## 5. Integrated senior-level capstone scenario

**Situation:** Two developers make conflicting changes while an infrastructure change needs additional review. A bad commit is then merged to the test branch, and an accidentally discarded local commit must be recovered.

Complete this in a **disposable test repository or sandbox branch**, not a production project:

1. Create the repository layout, contribution guide, ownership rules and a concise architecture decision.
2. Produce a conflicting change with two clones; choose and justify merge versus rebase.
3. Recover a discarded commit using its object ID or reflog, without rewriting shared history.
4. Identify the introduced regression using `git bisect`.
5. Open a pull/merge request affecting a sensitive path and demonstrate the configured approval or protection behaviour.
6. Explain how you would revert a faulty deployment-related change safely, and how GitOps would reconcile the result later in D05.

### Completion criteria

| Evidence | Standard |
| --- | --- |
| Git history | Correctly explain branches, merge bases, rewritten commits and the resulting graph |
| Recovery | Restore lost local work and identify a bad commit reproducibly |
| Repository design | Layout, `CONTRIBUTING.md`, CODEOWNERS or equivalent, and an ADR with trade-offs |
| Security | Ignore rules, secret-prevention controls and least-privilege decisions |
| Governance | Branch/review settings tested, with any enforcement limitations stated explicitly |
| Collaboration | A reviewed pull/merge request demonstrating the chosen integration policy |

**Pass standard:** You can explain **why** the controls and workflows were chosen, demonstrate they work (or clearly identify provider limits), and diagnose the consequences when they fail. Merely listing Git commands or uploading screenshots is insufficient.

## Optional deep dives

For developers already comfortable with the core work: `git worktree` for concurrent branches; `git rerere` for repeat conflict resolutions; `git range-diff` for assessing rebased series; signed commits and release tags; partial clone and sparse checkout; and policies for submodules versus monorepos. Explore these only where relevant to your own PDP.

## References

- [Pro Git — Git Internals](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
- [Pro Git — Branching](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell)
- [Git documentation — gitreflog](https://git-scm.com/docs/git-reflog)
- [Git documentation — git-bisect](https://git-scm.com/docs/git-bisect)
- [GitHub — Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub — CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitLab — Protected branches](https://docs.gitlab.com/user/project/repository/branches/protected/)

**Previous:** [DevOps Syllabus](DevOps_Syllabus.md) · **Next:** [D02 — Docker & Containerization](D02_Docker_and_Containerization.md)
