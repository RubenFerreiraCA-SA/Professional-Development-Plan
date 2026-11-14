# T-DEV-01-I — Intermediate Practice

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-i"></a>
#### T-DEV-01-I — Intermediate Practice

**Git is a graph of snapshots.** Each commit points at a tree (a directory snapshot) and at its parent commits. Objects are named by a hash of their content, so two commits with identical files but different parents, times or messages have different identities. That is why rewriting history is consequential even when the files look the same.

| Object or ref | Represents | Inspect with |
| --- | --- | --- |
| Blob | File content without its name | `git cat-file -p <id>` |
| Tree | Directory listing of names to blobs or trees | `git ls-tree HEAD` |
| Commit | A tree, parent ids, author and message | `git cat-file -p HEAD` |
| Annotated tag | Named release metadata pointing at an object | `git cat-file -p <tag>` |
| Ref | A readable name resolving to an object | `git show-ref` |

**Three places a change can live.** The *working directory* is what your editor shows. The *index* (staging area) is the next candidate snapshot. `HEAD` is the latest commit on the current branch. `git diff` compares working directory to index; `git diff --cached` compares index to `HEAD`; `git show HEAD` shows the last commit. They can legitimately all differ.

**Restore, reset and revert are not synonyms**

| Command | Intention | Scope |
| --- | --- | --- |
| `git restore <file>` | Discard working-tree edits to a file | Working directory |
| `git restore --staged <file>` | Unstage without losing edits | Index |
| `git reset --soft <commit>` | Move the branch, keep index and files | Ref only |
| `git reset --mixed <commit>` | Move the branch, reset the index | Ref and index |
| `git reset --hard <commit>` | Move the branch, reset index and tracked files | Destructive |
| `git revert <commit>` | Add a new commit that undoes an earlier one | History-preserving |

**Branches, HEAD and the merge base.** A branch is a pointer; `HEAD` says which one is checked out. The *merge base* is the most recent common ancestor of two branches:

```bash
git log --graph --decorate --oneline --all
git merge-base main feature/timeout
git diff main...feature/timeout     # changes on feature since it diverged
```

Three dots compare against the merge base; two dots compare the tips directly. They answer different questions. A *detached HEAD* means `HEAD` points at a commit rather than a branch; it is recoverable — create a branch there with `git switch -c rescue`.

**Four ways to integrate work**

| Strategy | Resulting history | Use when |
| --- | --- | --- |
| Merge commit | Both lines preserved, joined by a commit with two parents | You want topology and original commits visible. |
| Squash merge | One new commit on the target; the branch's commits are not ancestors | Small branches; you want a tidy mainline. |
| Rebase | Your commits replayed on a new base as *new* commits | Cleaning a private branch before review. |
| Cherry-pick | One commit's change copied to another branch | Backporting a fix to a release branch. |

No strategy is universally best. Choose based on review style, backporting needs, how builds trace to commits, and how quickly someone investigating an incident must read history.

**Conflicts are competing intentions.** A three-way merge compares *base*, *ours* and *theirs*. When both sides edited the same lines, Git stops rather than guess the meaning. Inspect the stages instead of trusting labels (during a rebase, "ours" and "theirs" swap sense):

```bash
git status
git ls-files -u                  # unmerged entries and stages 1/2/3
git show :1:config.yaml          # base
git show :2:config.yaml          # ours
git show :3:config.yaml          # theirs
git merge --abort                # safe way out of a merge in progress
```

Resolve by asking what each side was trying to achieve, run the tests, then commit. A resolution that compiles but drops one side's behaviour is a defect, not a resolution.

**Recovering work.** Moving a branch backwards does not delete the old commits immediately. The reflog records where refs pointed locally:

```bash
git reflog                         # find the lost commit
git branch recovery <commit-id>    # keep it, without rewriting shared refs
```

The reflog is local and expires; it is not a backup. For a bad commit already on a shared branch, use `git revert <sha>` and let it go through review. Do not reset and force-push a shared branch.

**Find the commit that broke something.** `git bisect` performs a binary search over history using a deterministic test:

```bash
git bisect start
git bisect bad HEAD
git bisect good v1.4.0
git bisect run ./scripts/regression-test.sh   # exit 0 = good, 1-127 = bad, 125 = skip
git bisect reset
```

**Exercise.** Using two clones of one repository, make conflicting edits to the same line, resolve the conflict by intent, then deliberately reset a branch hard, recover the lost commit through the reflog and revert a different commit on a pushed branch.
