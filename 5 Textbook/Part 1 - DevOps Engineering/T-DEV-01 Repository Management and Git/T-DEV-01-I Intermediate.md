# T-DEV-01-I — Intermediate Practice

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-i"></a>
#### T-DEV-01-I — Intermediate Practice

## Why this level exists

At Beginner level you can create commits and share a branch. Intermediate practice is about *understanding the graph you are building* so you can merge safely, recover from mistakes and collaborate without rewriting other people’s work by accident. If you only memorise commands, the first conflict or “lost” commit will feel mysterious. If you understand objects, refs and the three places a change can live, those situations become procedures.

If a term from Beginner is unfamiliar, skim [T-DEV-01-B](T-DEV-01-B%20Beginner.md#t-dev-01-b) for vocabulary, then return here.

## Git is a graph of snapshots

Each commit points at:

- a **tree** (a directory snapshot: names → blobs or nested trees)
- one or more **parent** commits
- author/committer metadata and a message

Objects are named by a cryptographic hash of their content. Two commits with identical files but different parents, times or messages have different identities. That is why “the code looks the same” is not the same as “it is the same commit”, and why rewriting history is consequential even when the files look unchanged.

| Object or ref | Represents | Inspect with |
| --- | --- | --- |
| Blob | File content without its path | `git cat-file -p <id>` |
| Tree | Directory listing of names → blobs/trees | `git ls-tree HEAD` |
| Commit | A tree, parent ids, author, message | `git cat-file -p HEAD` |
| Annotated tag | Named release metadata pointing at an object | `git cat-file -p <tag>` |
| Ref | A readable name resolving to an object (`refs/heads/main`) | `git show-ref` |

```bash
git cat-file -p HEAD          # see parents, tree, message
git ls-tree -r HEAD | head    # file paths in the snapshot
git rev-parse HEAD            # the commit id HEAD currently names
```

## Three places a change can live

| Place | What it is | Compare with |
| --- | --- | --- |
| Working tree | Files your editor shows | `git diff` (vs index) |
| Index (staging area) | Candidate next snapshot | `git diff --cached` (vs `HEAD`) |
| `HEAD` commit | Last committed snapshot on this branch | `git show HEAD` |

They can all differ at once. That is normal during careful work, not a bug.

**Mental model:** edit → stage the intentional slice → commit the slice → push when ready to share.

## Restore, reset and revert are not synonyms

| Command | Intention | Scope / risk |
| --- | --- | --- |
| `git restore <file>` | Discard working-tree edits to a tracked file | Working tree only |
| `git restore --staged <file>` | Unstage; keep file edits | Index |
| `git reset --soft <commit>` | Move branch tip; keep index and files | Ref only |
| `git reset --mixed <commit>` | Move tip; reset index to that commit | Ref + index (default) |
| `git reset --hard <commit>` | Move tip; reset index and tracked files | **Destructive** to local tracked edits |
| `git revert <commit>` | Add a *new* commit that undoes an earlier one | History-preserving; safe for shared branches |

Rule of thumb: if the commit is already on a shared branch that others use, prefer **revert**. Use **reset** on private work you have not pushed, or on a branch everyone agrees is yours alone.

## Branches, HEAD, merge bases and diffs that answer different questions

A branch is a pointer. `HEAD` says which pointer you have checked out. The **merge base** is the most recent common ancestor of two tips:

```bash
git log --graph --decorate --oneline --all
git merge-base main feature/timeout
git diff main...feature/timeout     # changes introduced on feature since it diverged
git diff main..feature/timeout      # direct tip-to-tip comparison (different question)
```

Three dots (`A...B`) compare against the merge base. Two dots (`A..B`) compare the tips. Mixing them up produces confusing reviews.

**Detached HEAD** means `HEAD` points at a commit rather than a branch name. Commits made there can look “lost” when you switch away. Recover by naming them:

```bash
git switch -c rescue
```

## Four ways to integrate work

| Strategy | Resulting history | Use when | Watch out for |
| --- | --- | --- | --- |
| Merge commit | Both lines preserved; join commit has two parents | You want topology and original commits visible | Noisier `main` graph |
| Squash merge | One new commit on the target; branch commits are not ancestors | Small branches; tidy mainline | Harder to bisect inside the squash |
| Rebase | Your commits replayed on a new base as *new* commits | Cleaning a **private** branch before review | Rewrites commit ids; never rebase shared published history casually |
| Cherry-pick | One commit’s change copied elsewhere | Backporting a fix to a release branch | Duplicate change under a new id; later merges can conflict or double-apply |

There is no universally best strategy. Choose based on review style, backport needs, how builds trace to commits, and how quickly someone investigating an incident must read history.

### Worked scenario: private rebase before review

```bash
git switch feature/add-health
git fetch origin
git rebase origin/main          # replay your commits on latest main
# resolve conflicts if prompted, then:
git rebase --continue
git push --force-with-lease     # only because this branch is yours alone
```

`--force-with-lease` refuses to overwrite the remote branch if someone else pushed commits you have not seen. Prefer it over bare `--force`.

## Conflicts are competing intentions

A three-way merge compares **base**, **ours** and **theirs**. When both sides edited the same region, Git stops rather than invent meaning.

```bash
git status
git ls-files -u                  # unmerged stages 1/2/3
git show :1:config.yaml          # base
git show :2:config.yaml          # ours
git show :3:config.yaml          # theirs
git merge --abort                # leave a merge safely
# during rebase, abort with:
git rebase --abort
```

During a rebase, the labels “ours” and “theirs” swap sense relative to a normal merge. Prefer inspecting stages (`:1:`, `:2:`, `:3:`) over trusting the words alone.

Resolve by asking what each side intended, run tests, then commit (merge) or `--continue` (rebase). A resolution that compiles but drops one side’s behaviour is a defect.

## Recovering work with the reflog

Moving a branch tip does not immediately delete old commits. The **reflog** records where refs pointed *on this machine*:

```bash
git reflog
git branch recovery <commit-id>
```

Limits: the reflog is local, expires, and is not a backup of other clones. For a bad commit already on a shared branch, use `git revert <sha>` through review. Do not reset and force-push a shared default branch.

### Worked recovery drill (safe on a disposable branch)

```bash
git switch -c drill/recovery
printf 'x\n' >> README.md
git add README.md && git commit -m "drill: temporary commit"
BAD=$(git rev-parse HEAD)
git reset --hard HEAD~1          # "lose" the commit from the branch tip
git reflog | head
git branch recovered $BAD
git switch recovered
git log -1 --oneline             # the commit is back under a name
```

## Finding the commit that introduced a bug: bisect

`git bisect` binary-searches history using a deterministic test:

```bash
git bisect start
git bisect bad HEAD
git bisect good v1.4.0           # a tag or commit known-good
# manually test each checkout, then:
git bisect good                  # or: git bisect bad
# or automate:
# git bisect run ./scripts/regression-test.sh
git bisect reset
```

The test must be deterministic: exit 0 for good, 1–127 for bad, 125 to skip untestable commits. If your “test” depends on flaky networks, bisect will lie.

## Pull requests as a review workflow

A pull request (or merge request) is a host feature: it proposes merging one branch into another and attaches discussion, checks and approvals. Intermediate skill is writing a reviewable change:

- keep the branch small and purposeful
- describe purpose, scope, test evidence and risk
- respond to review comments with new commits (or an agreed squash policy)
- do not force-push over commits under active review unless the team’s convention allows it (many teams rebase privately before review starts, then avoid rewriting)

```bash
git fetch origin
git switch main
git pull
git switch feature/add-health
git log --oneline main..HEAD     # commits unique to your branch
git diff main...HEAD             # patch unique to your branch since divergence
```

## Knowledge consolidation

- Commits are nodes in a **directed graph**; branches are movable labels.
- Know which of **working tree / index / HEAD** you are changing.
- Prefer **revert** on shared history; reserve **reset --hard** for private recovery.
- Conflicts are about **intent**; stages beat folklore about “ours/theirs”.
- The reflog rescues *local* mistakes; it is not organisational backup.

## Exercises

**Exercise 1.** Using two clones of one repository, make conflicting edits to the same line on two branches, merge, and resolve by documenting each side’s intent before editing. Abort once with `git merge --abort`, then repeat and finish the merge.

**Exercise 2 (challenge).** On a disposable branch, create three commits, `reset --hard` to drop them from the tip, recover them via reflog onto a new branch, then on a *pushed* branch use `git revert` (not reset) to undo a different commit and explain why the strategies differed.

**Solution notes.** Conflict markers must disappear before commit; `git ls-files -u` should be empty when you are done. After hard reset, `git reflog` should still show the lost tip for a time. Revert creates a forward commit; history still contains the original change plus its undo.
