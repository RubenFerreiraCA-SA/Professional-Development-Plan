# D02 — Advanced Git

| | Details |
| --- | --- |
| **Estimated study time** | 4–5 hours |
| **Prerequisites** | [D01 — Repository Fundamentals](D01_Repository_Fundamentals.md), routine branching and merging experience, and comfort using Git in a terminal. |

## Objective

Diagnose and recover difficult Git states, reason about commit history and design safe integration strategies for teams maintaining production software. Use disposable branches and clones for destructive experiments.

## Outcomes

1. Interpret commit objects, refs, the index, merge bases and history topology.
2. Explain the effects and trade-offs of merge, squash, rebase and cherry-pick.
3. Resolve non-trivial conflicts without rewriting shared history accidentally.
4. Recover discarded local work and identify regressions reproducibly.
5. Choose safe recovery strategies for published changes and explain the impact on delivery workflows.

## Suggested activities

| Activity | Estimated hours |
| --- | ---: |
| Git internals and history engineering | 1.5–2 |
| Conflicts, recovery and regression diagnosis | 1.5–2 |
| Practical Assessment and evidence | 1–1 |
| **Total** | **4–5** |

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

## 3. Practical Assessment — failure and recovery

In a disposable repository:

1. Create divergent histories, compare merge and squash results, and explain the chosen team integration policy.
2. Produce and resolve a conflict from two separate clones; document your choice of merge or rebase.
3. Recover an intentionally discarded **local** commit using a reflog or recorded object ID.
4. Introduce a regression across several commits and identify the first bad commit with `git bisect`.
5. Explain how you would revert a faulty published change safely and how GitOps reconciliation will be explored in [D06](D06_GitOps_Automation_and_Operations.md).

**Completion standard:** Show the relevant commit graphs, the recovered change and the bisect result. Explain why the recovery is safe for a shared team repository.

## Optional deep dives

Explore `git worktree`, `git rerere`, `git range-diff`, signed commits and tags, sparse checkout or partial clone where useful to your own PDP.

## References

- [Pro Git — Git Internals](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
- [Pro Git — Branching](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell)
- [Git documentation — gitreflog](https://git-scm.com/docs/git-reflog)
- [Git documentation — git-bisect](https://git-scm.com/docs/git-bisect)
- [GitHub — Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub — CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitLab — Protected branches](https://docs.gitlab.com/user/project/repository/branches/protected/)

**Previous:** [D01 — Repository Fundamentals](D01_Repository_Fundamentals.md) · **Next:** [D03 — Docker & Containerization](D03_Docker_and_Containerization.md)
