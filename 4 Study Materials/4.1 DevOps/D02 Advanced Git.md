# Chapter 2 — Advanced Git (D02)

*DevOps Engineering textbook · Chapter 2 of 8*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [D02 course detail](../../3%20Course%20Detail/3.1%20DevOps/D02%20Advanced%20Git.md) for its provisional estimate. |
| **Prerequisites** | [D01 — Repository Fundamentals](D01%20Repository%20Fundamentals.md), regular use of branches, commits and pull/merge requests, and confidence in a terminal. |

## How to study this chapter

The purpose of Advanced Git is not to memorise more commands. It is to **predict what Git will do, recognise what has happened, and repair mistakes without endangering a shared delivery system**.

Work through the sections in order. Each one adds a layer to your mental model and asks you to **understand → inspect → practise → verify → explain**. The worked examples use a small application inspired by the **Harbour API** repository from D01. You can bring the lessons back to that Final Project repository, but use **disposable local repositories for all history rewriting, conflict and recovery drills**. Never reproduce a destructive exercise on a real team's `main` branch.

This text teaches the requirements defined in [D02 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D02%20Advanced%20Git.md), which remains the authoritative outline. The [D00 DevOps Syllabus](../../3%20Course%20Detail/3.1%20DevOps/D00%20DevOps%20Syllabus.md) describes how D02 connects to the larger programme.

### Learning outcomes

By the final chapter you should be able to:

1. Explain blobs, trees, commits, refs, `HEAD`, the index, the working tree and reflogs using evidence from a repository.
2. Predict the history consequences of merge, squash merge, rebase and cherry-pick, and choose an appropriate integration policy.
3. Diagnose conflicting changes using a real two-clone collaboration scenario.
4. Recover lost *local* commits and reverse faulty *published* changes using different, safe techniques.
5. Identify a regression with `git bisect` and produce a useful engineering incident report.

### Before you begin

Check that Git is installed and that you have space for temporary repositories:

```bash
git --version
git config --get user.name
git config --get user.email
```

If the identity values are missing, configure an identity **in each training repository** when prompted (do not invent a company identity). The examples assume a modern Git supporting `git switch` and `git restore`. All illustrations refer to local sample commits; your abbreviated hashes will differ.

Use a dedicated disposable directory. The command below avoids accidentally mixing these exercises with your existing Final Project:

```bash
mkdir -p ~/git-learning-lab
cd ~/git-learning-lab
pwd
```

---

## Section 2.1 — A Git commit is a snapshot in a graph

### 2.1.1 Why a mental model matters

Git is a *distributed version-control system*. It tracks snapshots of files and the relationships between those snapshots. A branch is not a separate directory containing a second copy of your project: it is a movable name that normally points to a commit.

This distinction explains several confusing behaviours. A `reset` can move a branch without deleting its old commit immediately; a `rebase` can give apparently identical changes different commit identifiers; and a `merge` can preserve two lines of development without putting all commits in a straight line.

Imagine the following graph:

```text
A --- B --- C            main
       \
        D --- E          feature
```

Each letter is a commit, and the lines show **parent relationships**. Commit `D` has `B` as its parent; `E` has `D` as its parent. `C` and `E` share an ancestor, `B`, but neither is necessarily a descendant of the other. A label such as `main` just tells you which commit a ref currently names.

### 2.1.2 Git's four important object concepts

Git stores content in an object database, usually under `.git/objects`:

| Object or ref | What it represents | Useful inspection |
| --- | --- | --- |
| **Blob** | File content, without its pathname | `git cat-file -p <blob-id>` |
| **Tree** | Directory entries linking names to blobs or subtrees | `git ls-tree HEAD` |
| **Commit** | A root tree, parent commit IDs, author/committer details and message | `git cat-file -p HEAD` |
| **Annotated tag** | Named release metadata pointing at an object | `git cat-file -p <tag-object-id>` |
| **Ref** | A human-readable name resolving to an object (e.g. `refs/heads/main`) | `git show-ref` |

Object IDs are content-derived. Even if two commits point to equivalent file trees, differences in parents, timestamps, metadata or messages generally give them distinct identities. This is why rewriting history is consequential even when the resulting files look the same.

### 2.1.3 Worked example: create and inspect objects

Create a *fresh* local training repository:

```bash
cd ~/git-learning-lab
mkdir -p objects-demo
cd objects-demo
git init -b main
git config user.name "Training Developer"
git config user.email "training@example.invalid"

mkdir app
printf 'status=healthy\n' > app/service.txt
git add app/service.txt
git commit -m "feat: establish health status"
printf 'timeout=5\n' >> app/service.txt
git add app/service.txt
git commit -m "feat: configure timeout"
```

Now investigate:

```bash
git log --graph --decorate --oneline --all
git cat-file -t HEAD
git cat-file -p HEAD
git ls-tree -r HEAD
git rev-parse HEAD^{tree}
git show HEAD:app/service.txt
```

Read the output deliberately:

- `git cat-file -t HEAD` says **commit**, because `HEAD` currently resolves to a commit.
- `git cat-file -p HEAD` displays a `tree` line and a `parent` line. The first commit in this new repository has **no parent**.
- `git ls-tree -r HEAD` walks the snapshot and lists the blob object associated with `app/service.txt`.
- `git show HEAD:app/service.txt` reads the file content from the commit, which may be different from the current working directory later.

### Exercise 2.1

Change only the commit message of a new local throwaway commit using `git commit --amend`, then compare the old and new commit IDs. **Do this only for a commit that has not been published.** Explain why changing a message changes the object's identity even if its file tree is unchanged.

### Check your understanding

Can two commits have the same tree ID but different commit IDs? **Yes:** their snapshots may be identical while their parent links or commit metadata differ.

Can `git status` tell you everything about whether a commit has been published? **No:** it shows working-tree/index state and, when configured, comparison with an upstream; you must inspect the relevant refs and remote.

---

## Section 2.2 — Three trees: working directory, index and committed snapshot

### 2.2.1 The three places a change can exist

A useful everyday model is:

```text
Working directory       Index (staging area)      HEAD commit
files you edit   --add--> intended next snapshot --commit--> saved snapshot
```

The working directory is what your editor sees. The **index** records the next candidate snapshot. `HEAD` normally resolves to the current branch's latest commit.

The difference between these explains why `git diff`, `git diff --cached` and `git show HEAD` can display different content.

### 2.2.2 Worked example: stage one version, edit another

In `objects-demo`:

```bash
printf 'timeout=10\n' >> app/service.txt
git add app/service.txt
printf 'retry=2\n' >> app/service.txt

git status --short
git diff -- app/service.txt
git diff --cached -- app/service.txt
```

**Expected observation:** The short status will show both staged and unstaged modifications for the file (often `MM`). The cached diff contains `timeout=10`; the unstaged diff contains the newer `retry=2` line. If you commit now, the staged snapshot **does not include** `retry=2` unless you stage again.

This matters in platform repositories: a developer may believe they are reviewing one configuration while the index contains another.

### 2.2.3 Restore, reset and revert are not synonyms

| Command | Primary intention | Typical scope |
| --- | --- | --- |
| `git restore <file>` | Restore working-tree content from the index | Working directory |
| `git restore --staged <file>` | Unstage changes by restoring index content from `HEAD` | Index |
| `git reset --soft <commit>` | Move current branch ref while retaining index and working tree | Ref |
| `git reset --mixed <commit>` | Move current branch and reset index | Ref and index |
| `git reset --hard <commit>` | Move branch, reset index and tracked working-tree files | Potentially destructive |
| `git revert <commit>` | Create a new change that attempts to reverse an earlier commit | History-preserving |

These commands are context-sensitive. For example, `git reset --hard` can discard uncommitted tracked-file changes; it does not necessarily erase every untracked file. Never use it as a reflexive “cleanup” step.

### Exercise 2.2

In your sandbox, save the output of the staged and unstaged diffs. Then run:

```bash
git restore --staged app/service.txt
git diff -- app/service.txt
git status --short
```

**Expected:** The changes are now unstaged; both added lines appear in the working-tree diff. Commit them only after reviewing the exact file content:

```bash
git add app/service.txt
git diff --cached --check
git commit -m "feat: tune service behaviour"
```

### Engineering question

Which action is safest when an already-published deployment configuration must be rolled back: moving `main` backward or recording a new reverting commit? In normal shared-branch workflows, **a new revert commit** preserves the reviewed history and gives GitOps an explicit desired-state change. D06 explores the deployment consequences.

---

## Section 2.3 — Refs, HEAD, history and the merge base

### 2.3.1 Branches are pointers; HEAD tells you what is checked out

Most of the time, `HEAD` is a symbolic reference to a branch such as `refs/heads/main`. When you check out a specific commit rather than a branch, you enter **detached HEAD** state. You can inspect and even commit there, but those new commits are not automatically named by a long-lived branch.

Build a feature history:

```bash
cd ~/git-learning-lab/objects-demo
git switch -c feature/health-details
printf 'status=degraded\n' > app/status-example.txt
git add app/status-example.txt
git commit -m "docs: add degraded status example"
git switch main
printf 'owner=platform\n' > app/owner.txt
git add app/owner.txt
git commit -m "docs: record service owner"
git log --graph --decorate --oneline --all
```

The feature and `main` now have independent commits after their common starting point.

### 2.3.2 Find a common ancestor

```bash
git merge-base main feature/health-details
git diff main..feature/health-details
git diff main...feature/health-details
```

The **merge base** is a best common ancestor. For ordinary divergent history:

- `git diff main..feature` compares the **two endpoint snapshots** (`main` to `feature`).
- `git diff main...feature` compares the **merge-base snapshot** to the feature endpoint. This often better represents “what the feature introduced since the branches diverged.”

A three-dot *diff* is not the same as a three-dot *log*. Git uses the notation differently depending on the command; always check what question a command answers.

### 2.3.3 Detached HEAD: a recoverable state, not a catastrophe

```bash
git switch --detach HEAD~1
git status --short --branch
git log -1 --oneline
git switch main
```

**Expected:** Git reports a detached HEAD while inspecting the earlier commit. Switching back to `main` restores branch context without rewriting history.

If you intentionally create useful commits while detached, preserve them with a new branch **before they become difficult to find**:

```bash
git switch -c saved/experiment
```

Use the command *while still at that detached commit*. Otherwise identify the old commit via reflog first.

### Exercise 2.3

Draw your actual branch graph with four or five commit IDs and show the parent of each non-root commit. Explain which diff range a reviewer should use and why. Save the merge-base ID and a short decision note.

### Platform insight

Understanding commit ancestry helps when an artifact is deployed from an unexpected SHA or a pull request appears to include unrelated commits. The fix might be a wrong merge base or source branch—not a broken CI pipeline.

---

## Section 2.4 — Merge, squash merge, rebase and cherry-pick

### 2.4.1 Four strategies, four different histories

Suppose the graph is:

```text
A --- B --- C      main
       \
        D --- E    feature
```

**Merge commit:** Integrate two parent histories, typically producing `M` with parents `C` and `E`. Existing commits remain identifiable.

```text
A --- B --- C ------- M   main
       \             /
        D ---------- E   feature
```

**Squash merge:** Apply the feature's combined change as a *new* commit on `main`. The resulting mainline is simple, but `D` and `E` are not individual ancestors of that squash commit.

**Rebase:** Replay `D` and `E` on `C` as new commits, say `D'` and `E'`. The old and new commits may represent similar patches but have different parents and object IDs.

**Cherry-pick:** Replay one selected commit's change on another branch. Useful for a narrowly scoped backport, but it duplicates the logical change under a different commit ID and can cause conflicts later.

No strategy is universally superior. Teams should consider collaboration style, auditability, backports, GitOps reconciliation and cost of investigating production incidents.

### 2.4.2 A reproducible comparison

Rather than modify the D01 repository, build two independent copies of a small history:

```bash
cd ~/git-learning-lab
mkdir -p integration-demo
cd integration-demo
git init -b main
git config user.name "Training Developer"
git config user.email "training@example.invalid"
printf 'mode=normal\n' > config.txt
git add config.txt
git commit -m "chore: baseline configuration"
git switch -c feature/retries
printf 'retries=2\n' >> config.txt
git add config.txt
git commit -m "feat: add retries"
printf 'backoff=exponential\n' >> config.txt
git add config.txt
git commit -m "feat: add backoff"
git switch main
printf 'owner=platform\n' > owner.txt
git add owner.txt
git commit -m "docs: specify owner"
```

First, merge normally:

```bash
git switch -c demo/merge main
git merge --no-ff feature/retries -m "merge: feature/retries"
git log --graph --decorate --oneline --all
```

Then independently squash the same feature onto the original mainline:

```bash
git switch -c demo/squash main
git merge --squash feature/retries
git commit -m "feat: retries with backoff"
git log --graph --decorate --oneline --all
```

Inspect the parent counts:

```bash
git rev-list --parents -n 1 demo/merge
git rev-list --parents -n 1 demo/squash
git diff demo/merge demo/squash
```

**Expected:** The merge commit has two parent IDs, while the squash commit has one. Because the two integrations start from the same `main` and apply the same feature changes, their resulting file snapshots should be equivalent, so the final diff should be empty.

### 2.4.3 Explore rebase without rewriting a shared branch

Create a **new, disposable copy** of the feature branch at its original tip and replay it onto `main`:

```bash
git switch -c demo/rebase feature/retries
git rebase main
git log --graph --decorate --oneline --all
git rev-parse feature/retries
git rev-parse demo/rebase
```

**Expected:** `demo/rebase` ends at new commit IDs; the original `feature/retries` ref is unchanged. The `demo/rebase` branch begins from `main` and contains replayed feature commits.

### 2.4.4 Cherry-pick for backports

Create a new branch from the baseline and selectively replay a feature commit:

```bash
git switch -c demo/backport main
git log --oneline feature/retries
```

Identify the *earlier* `feat: add retries` commit, then:

```bash
git cherry-pick <RETRIES-COMMIT-ID>
git log --oneline -3
```

**Expected:** The backport gains the retries change, but not the later backoff change. The cherry-picked commit has a new ID because its parent is different.

### Exercise 2.4 — an integration policy ADR

Compare your four histories and answer:

- Which preserves the feature's individual commit IDs in `main`?
- Which minimises visible mainline commits?
- Which approach would you avoid for an already-shared branch?
- How would you backport a security fix while minimising unrelated changes?
- Which record best supports an incident investigator tracing a deployment to reviewed source?

Write a short `docs/decisions/0002-integration-policy.md` in the *real* Harbour repository, if you want this assessment evidence to feed the Final Project. Do not copy sandbox history into it.

---

## Section 2.5 — Conflicts are competing intentions, not just broken text

### 2.5.1 How a three-way merge works

Git compares **base**, **ours** and **theirs** versions of content. When two branches edit overlapping text, Git may not know the intended combined result. It pauses rather than inventing the application's meaning.

During an ordinary merge:
- Stage **1** is the merge base.
- Stage **2** is ours (normally your currently checked-out branch).
- Stage **3** is theirs (the branch being merged).

For rebases, “ours” and “theirs” can be counterintuitive because the replayed commit is being applied onto another base. Never make a decision using the label alone; inspect the stages and graph.

### 2.5.2 Simulate two developers with two clones

This is an intentionally **local-only collaboration test**. It uses a bare repository as a shared remote, avoiding the need for credentials or a hosted service.

```bash
cd ~/git-learning-lab
mkdir -p conflict-lab
cd conflict-lab
git init --bare --initial-branch=main origin.git
git clone origin.git alice
cd alice
git config user.name "Alice Training"
git config user.email "alice@example.invalid"
printf 'timeout=5\n' > settings.conf
git add settings.conf
git commit -m "chore: baseline timeout"
git push -u origin main
cd ..
git clone origin.git bob
cd bob
git config user.name "Bob Training"
git config user.email "bob@example.invalid"
```

Alice changes the same line in one direction:

```bash
cd ../alice
printf 'timeout=10\n' > settings.conf
git add settings.conf
git commit -m "feat: extend timeout for slow clients"
git push
```

Bob independently changes the line another way, *without fetching Alice's new commit*:

```bash
cd ../bob
printf 'timeout=3\n' > settings.conf
git add settings.conf
git commit -m "feat: reduce timeout for fast failures"
git fetch origin
git log --graph --decorate --oneline --all
git merge origin/main
```

**Expected:** The merge reports a content conflict in `settings.conf`. Git does not automatically accept either value. This is a **training repository**, so the conflict is safe to explore.

Inspect the evidence:

```bash
git status
git ls-files -u
git show :1:settings.conf
git show :2:settings.conf
git show :3:settings.conf
cat settings.conf
```

You should see the base `timeout=5`, Bob's version `timeout=3` and Alice's version `timeout=10`. The working file contains conflict markers.

### 2.5.3 Resolve by engineering intent

A resolver should not choose `timeout=10` merely because it was “theirs”, nor `timeout=3` because it was “ours”. The decision depends on request latency, retry budgets, upstream failure characteristics and product requirements.

For the exercise, assume the agreed system contract requires a maximum of 8 seconds. Neither edit is correct by itself: set the file to `timeout=8`, record why, and complete the merge.

```bash
printf 'timeout=8\n' > settings.conf
git add settings.conf
git diff --cached --check
git merge --continue
git log --graph --decorate --oneline --all
```

If the editor opens for the merge message, save and close it. For a *merge* conflict, `git merge --continue` (or `git commit`) completes the operation. `git rebase --continue` belongs to a rebase and is **not** interchangeable.

**Expected:** The merge commit has two parents and the resolved file contains exactly `timeout=8`.

### 2.5.4 Abort and re-attempt safely

In a fresh throwaway clone, recreate a similar conflict and run `git merge --abort`. Confirm the branch returns to its pre-merge state. A rebase stopped in conflict is instead aborted with `git rebase --abort`.

Do not run abort commands blindly if you have unrelated uncommitted work. Inspect `git status` and save work safely *before* starting complex operations.

### Exercise 2.5

Create a second conflict involving a deployment manifest's replica count or health timeout. Write a five-sentence resolution note: base, competing intentions, chosen result, validation and operational risk.

### Check your understanding

Is a syntactically conflict-free merge automatically correct? **No.** Two changes can merge without textual conflict and still violate a business or infrastructure invariant. Automated tests, code-owner review and architectural context remain necessary.

---

## Section 2.6 — Recovering work and undoing mistakes

### 2.6.1 A ref moves; objects do not instantly vanish

A branch points at a commit. If you move the branch backward, previously referenced commits may become unreachable from branch heads, but can often be found through the **reflog**. Reflogs are local records of ref movement and are subject to expiration and garbage collection; they are not an indefinite backup or a reliable record stored on every remote.

This explains why the correct recovery technique depends on whether work was **local/unpublished** or **published/shared**.

### 2.6.2 Recover an intentionally discarded local commit

Use a separate repository for this destructive demonstration:

```bash
cd ~/git-learning-lab
mkdir -p recovery-lab
cd recovery-lab
git init -b main
git config user.name "Training Developer"
git config user.email "training@example.invalid"
printf 'baseline\n' > recovery.txt
git add recovery.txt
git commit -m "chore: baseline"
git switch -c sandbox/lost-commit
printf 'important local change\n' >> recovery.txt
git add recovery.txt
git commit -m "feat: important local change"
git log -2 --oneline
```

Copy the newest commit ID into your notes, then **only in this disposable branch**:

```bash
git reset --hard HEAD~1
git log -2 --oneline
git reflog -5
```

The important commit no longer appears in the current branch history, but you should find it in the reflog. Restore a named branch pointing to the discarded commit:

```bash
git branch recovered/important <LOST-COMMIT-ID>
git show recovered/important:recovery.txt
git log --oneline --all --graph
```

**Expected:** The recovered branch contains the original change, while `sandbox/lost-commit` remains at the earlier commit. Creating a branch is preferable to immediately rewriting another history. It also preserves the recovered commit against becoming unreachable.

If your reflog cannot locate the commit, investigate `git fsck --unreachable` in a disposable environment; understand that pruning and garbage collection can make retrieval impossible.

### 2.6.3 Published history calls for revert

Suppose a broken configuration commit has already been merged and teammates may have fetched it. Moving a shared branch backward with `reset` and force-pushing would invalidate other people's assumptions and potentially bypass the team's review policy.

Instead, create a **new commit** that reverses the old change:

```bash
cd ~/git-learning-lab
mkdir -p revert-lab
cd revert-lab
git init -b main
git config user.name "Training Developer"
git config user.email "training@example.invalid"
printf 'feature=off\n' > flags.conf
git add flags.conf
git commit -m "chore: baseline"
printf 'feature=on\n' > flags.conf
git commit -am "feat: enable feature"
git log --oneline -2
git revert --no-edit HEAD
git log --oneline -3
cat flags.conf
```

**Expected:** The latest commit is a revert; the file content returns to `feature=off`. The original feature commit **still exists in history**. `git revert` may conflict if later changes overlap, and reverting merge commits requires a deliberate mainline-parent choice.

### 2.6.4 Compare the correct recovery tools

| Situation | Prefer | Why |
| --- | --- | --- |
| Unstaged local edit you want to discard | `git restore` with an appropriate source | Changes working-tree content |
| Staged change included by mistake | `git restore --staged` | Changes the index without deleting working edits |
| Local, unpublished commits need reorganising | Carefully chosen reset/rebase on a private branch | Shared consumers are not affected |
| Locally lost commit still in reflog | New recovery branch at its object ID | Preserves evidence without rewriting shared refs |
| Bad change already on protected `main` | Reviewed `git revert` commit | Keeps shared history and makes rollback auditable |
| Credential leaked into history | Revoke/rotate first, then coordinated response | Removing the latest line does not unexpose the credential |

### Exercise 2.6

Write a short incident response for each scenario above. For a published bad deployment configuration, explain how reverting the *desired-state commit* will later interact with GitOps (D06). Note that reversing configuration does **not** undo irreversible data migrations or side effects.

### Safety checkpoint

Do not use `git push --force` to repair a protected production branch. Even `--force-with-lease` is not a replacement for branch protection and proper review; it is a narrower guard for exceptional, authorised history rewriting.

---

## Section 2.7 — Find the first bad commit with git bisect

### 2.7.1 Regression debugging as binary search

A regression means a behaviour that previously worked now fails. If you know one **good** commit and one **bad** commit, `git bisect` checks commits along the ancestry path to narrow down the first bad one.

This works best when:
- The behaviour can be tested consistently.
- You can identify a known-good starting revision.
- The test meaningfully distinguishes good and bad states.
- The tested revisions are buildable, or you can explicitly skip untestable revisions.

Git bisect does not automatically explain *why* a commit caused the bug. It identifies a candidate to investigate.

### 2.7.2 Build an intentionally failing history

Create a deterministic shell test and several commits:

```bash
cd ~/git-learning-lab
mkdir -p bisect-lab
cd bisect-lab
git init -b main
git config user.name "Training Developer"
git config user.email "training@example.invalid"

printf 'timeout=5\n' > settings.conf
printf '#!/bin/sh\nset -eu\nvalue=$(cut -d= -f2 settings.conf)\n[ "$value" -le 8 ]\n' > verify.sh
chmod +x verify.sh
git add settings.conf verify.sh
git commit -m "test: establish healthy timeout"
GOOD=$(git rev-parse HEAD)

printf 'retries=2\n' > retries.conf
git add retries.conf
git commit -m "feat: add retry policy"

printf 'timeout=20\n' > settings.conf
git add settings.conf
git commit -m "feat: increase timeout beyond contract"

printf 'owner=platform\n' > owner.conf
git add owner.conf
git commit -m "docs: record owner"
./verify.sh || echo "Current revision fails, as intended"
```

The shell test exits with success if the timeout is at most 8 and failure otherwise. The first commit was good; the third commit introduced the failure.

### 2.7.3 Run bisect

```bash
git bisect start
git bisect bad HEAD
git bisect good "$GOOD"
```

At each checked-out commit, run:

```bash
./verify.sh
```

If the test succeeds, run `git bisect good`. If it fails, run `git bisect bad`. Repeat until Git identifies the first bad commit. You can automate the exact same repeatable test:

```bash
git bisect reset
git bisect start HEAD "$GOOD"
git bisect run ./verify.sh
git bisect log
git bisect reset
```

**Expected:** Git identifies `feat: increase timeout beyond contract` as the first bad commit. `git bisect reset` returns you to your original checked-out state.

### 2.7.4 More realistic complications

In production, some commits may be unbuildable or depend on unavailable infrastructure. A test may be flaky, or multiple commits might interact. Under such circumstances, `git bisect skip` can omit an untestable revision, but may leave the result ambiguous.

Also distinguish **first bad commit** from **root cause**. The identified change may merely expose an older defect or violate an unstated contract.

### Exercise 2.7

Change the test to check an environment-independent application behaviour. Run bisect again and capture the bisect log. Then explain what extra evidence would be needed before reverting a commit in production.

---

## Section 2.8 — Engineering history policies for a platform team

### 2.8.1 Git history is an operational asset

A platform team will eventually need to answer: *Which change led to this deployed artifact? Who reviewed the change? Was it backported? Can we roll it back safely?* An integration policy should support these questions without slowing every developer down.

Consider:

- **Traceability:** A deployed image built from a specific SHA should be associated with a reviewed change.
- **Auditability:** A reviewer and an incident responder must reconstruct the change history.
- **Reproducibility:** The source reference used by CI must not silently move during an immutable release.
- **Coordination:** Multiple maintainers should not be forced to recover from routine history rewrites.
- **Developer experience:** The workflow should be straightforward enough that teams use it consistently.

### 2.8.2 A practical policy decision

For Harbour Platform, compare two proposals:

**Policy A:** Require all changes via pull/merge requests; keep merge commits for complicated feature work, squash very small branches and disallow force-push to `main`.

**Policy B:** Require all integration branches to be rebased and fast-forwarded to maintain a completely linear history.

Neither is inherently wrong. Policy A retains some topology and makes branch integration visible; Policy B simplifies history traversal but requires careful management of shared feature branches and review assumptions.

Decide which fits an application-plus-platform repository. Document assumptions: number of maintainers, review rules, release tagging, backports, and how the build system associates artifacts with commits.

### 2.8.3 Optional advanced techniques

These topics go beyond the core assessment but are useful when a real problem requires them:

- `git worktree`: Keep more than one branch checked out in separate working directories.
- `git rerere`: Reuse previously recorded conflict resolutions; verify the result before trusting it.
- `git range-diff`: Compare two versions of a patch series after a rebase.
- Signed commits/tags: Support identity/provenance checks, but do not imply content safety.
- Sparse checkout and partial clone: Reduce local checkout scope for large repositories.
- Submodules versus monorepos: Different dependency, versioning and operational trade-offs.

For one optional topic, record the **problem it solves**, a small test and **the operational risk it introduces**.

---

## Practical Assessment — Chapter 2 — history, collaboration and recovery

**Scenario:** The Harbour Platform team has two developers editing shared configuration. One change conflicts with another. A local commit disappears during maintenance. A later configuration change introduces a regression into a test branch. The team must recover without rewriting protected shared history.

Use a **disposable repository and local bare remote**, or another authorised test environment. Do not create these failures in the actual Final Project repository.

### Deliverables

1. **History model:** An annotated commit graph showing a merge base, divergent branches and parent relationships, using real command output.
2. **Integration comparison:** Merge-commit and squash-merge examples with reasoning about file-tree equality, traceability and a chosen team policy. Demonstrate rebase or cherry-pick in a separate sandbox branch.
3. **Concurrent-development scenario:** Two separate clones producing an actual conflict. Show stages 1/2/3, the agreed functional resolution and the resulting commit graph.
4. **Safe recovery:** Recovered local commit from an object ID or reflog onto a *new* branch, without rewriting the shared default branch.
5. **Regression investigation:** Reproducible `git bisect` test, bisect log, identified first bad commit and a clear distinction between culprit and root-cause evidence.
6. **Operational response:** A proposed reviewed `git revert` approach for a published bad change, including what must be checked when the change affects GitOps or data.
7. **Engineering decision:** A short ADR for a repository integration policy, including developer friction, release traceability and risks of shared history rewriting.

### Evaluation rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Git internals | Lists terminology | Explains object, ref, index and parent relationships with command evidence | Uses the model to predict unexpected states |
| Integration | Runs merge commands by habit | Selects strategy based on resulting history and team requirements | Explicitly manages backports, traceability and review consequences |
| Conflict handling | Picks one side mechanically | Explains base and competing intentions, validates correct result | Identifies non-textual and runtime compatibility risks |
| Recovery | Uses reset indiscriminately | Recovers local work and proposes revert for shared history | Preserves forensic evidence and anticipates downstream systems |
| Debugging | Guesses which commit broke the service | Uses a deterministic bisect test and verifies the candidate | Explains uncertainty, flaky tests and root-cause follow-up |
| Communication | Provides screenshots only | Produces reproducible steps, a decision record and incident notes | A second engineer independently repeats key diagnoses |

**Completion standard:** Achieve **Competent** in every row, with reproducible evidence. An Advanced result is welcome but not required. There is no grade for speed.

### Self-check before submitting

- Can you explain why two commits with identical trees may still have different IDs?
- Can you read the index and working-tree differences before committing?
- Do you know when rebase rewrites commit identities?
- Can you resolve a conflict according to intended behaviour rather than choosing one text block?
- Can you preserve a recovered commit without modifying `main`?
- Can you separate “first bad commit” from “proven root cause”?
- Can another engineer repeat your important steps using only your notes?

### Example of an acceptable assessment conclusion

> We chose reviewed merge commits for complex cross-team changes and squash merge for short-lived documentation branches. The shared default branch is never force-pushed. We resolved a concurrent timeout conflict by checking the documented service contract rather than choosing a developer's version. A discarded local commit was recovered via reflog onto a new branch. Bisect isolated the first failing configuration commit; we would propose a reviewed revert and verify application and GitOps consequences before promotion.

The conclusion alone is **not** proof; it must be backed by the working repositories and verification evidence above.

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| See how changes diverged | `git log --graph --decorate --oneline --all`, `git merge-base` | Guessing from branch names |
| Review a feature relative to divergence | `git diff main...feature` | Assuming two-dot and three-dot mean the same |
| Inspect what will be committed | `git diff --cached` | Assuming your editor shows staged content |
| Investigate a conflict | `git status`, `git ls-files -u`, `git show :1:...` | Choosing ours/theirs without understanding intent |
| Recover lost unpublished work | `git reflog`, create recovery branch | Force-pushing shared refs |
| Undo a published change | New reviewed `git revert` | Resetting and rewriting shared history |
| Find a regression | Deterministic test and `git bisect` | Blaming the most recent commit without evidence |

## Glossary

| Term | Definition |
| --- | --- |
| Blob | Git object containing file data |
| Tree | Git object connecting names to blobs and subtrees |
| Commit | Git object identifying a snapshot, parents and metadata |
| Ref | Named reference to an object, commonly a branch |
| HEAD | Reference indicating the current checkout |
| Index | Staged snapshot intended for the next commit |
| Merge base | Common ancestor used in merging and comparisons |
| Reflog | Local history of ref updates, subject to expiry |
| Detached HEAD | Checkout of a commit without a branch name |
| Rebase | Replay commits on a different base as new identities |
| Cherry-pick | Apply a chosen commit's change on another branch |
| Revert | New commit attempting to undo another commit's effect |
| Bisect | Search for an introducing regression between good and bad revisions |

## References

- [Pro Git — Git internals](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
- [Pro Git — Git branching](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell)
- [Git documentation — git-diff](https://git-scm.com/docs/git-diff)
- [Git documentation — git-reflog](https://git-scm.com/docs/git-reflog)
- [Git documentation — git-merge](https://git-scm.com/docs/git-merge)
- [Git documentation — git-rebase](https://git-scm.com/docs/git-rebase)
- [Git documentation — git-bisect](https://git-scm.com/docs/git-bisect)
- [GitHub — Branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitLab — Protected branches](https://docs.gitlab.com/user/project/repository/branches/protected/)

**Previous chapter:** [Chapter 1 — Repository Fundamentals](D01%20Repository%20Fundamentals.md) · **Course detail:** [D02 — Advanced Git](../../3%20Course%20Detail/3.1%20DevOps/D02%20Advanced%20Git.md) · **Next chapter:** Chapter 3 — Docker and Containerization (not yet authored)
