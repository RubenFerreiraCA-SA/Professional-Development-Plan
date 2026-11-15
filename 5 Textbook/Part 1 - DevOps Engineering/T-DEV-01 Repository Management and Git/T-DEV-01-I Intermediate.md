# T-DEV-01-I — Intermediate Practice

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-i"></a>
#### T-DEV-01-I — Intermediate Practice

## Why this level exists

At Beginner level you can create commits and share a branch. Intermediate practice is about *understanding the graph you are building* so you can merge safely, recover from mistakes and collaborate without rewriting other people’s work by accident. If you only memorise commands, the first conflict or “lost” commit will feel mysterious. If you understand objects, refs and the three places a change can live, those situations become procedures.

If a term from Beginner is unfamiliar, skim [T-DEV-01-B](T-DEV-01-B%20Beginner.md#t-dev-01-b) for vocabulary, then return here. Outputs shown below are *illustrative*: hashes and timestamps will differ on your machine. Every lab uses a throwaway repository, and each ends with a check you can run so you know the lab worked.

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

### Lab: walk the object graph by hand

Build a tiny repository so every object is small enough to read:

```bash
mkdir graph-lab && cd graph-lab && git init -b main
mkdir src && printf 'print("v1")\n' > src/app.py && printf '# Lab\n' > README.md
git add . && git commit -m "first"
printf 'print("v2")\n' > src/app.py && git commit -am "second"
```

Step 1 — read the commit:

```bash
git cat-file -p HEAD
```

Illustrative output:

```text
tree 9c1f0e2a7b6d4e5f8a3b2c1d0e9f8a7b6c5d4e3f
parent 4a2b7c1d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b
author Sam Example <sam@example.com> 1731650000 +0200
committer Sam Example <sam@example.com> 1731650000 +0200

second
```

Step 2 — follow the `tree` line, then follow a path through it:

```bash
git cat-file -p HEAD^{tree}
git cat-file -p HEAD:src
git cat-file -p HEAD:src/app.py
git cat-file -t HEAD:src/app.py
```

Illustrative output of the first command:

```text
100644 blob 7e5f2a9c3b1d4e6f8a0b2c4d6e8f0a1b3c5d7e9f	README.md
040000 tree 2d4f6a8c0e1b3d5f7a9c1e3b5d7f9a0c2e4b6d8f	src
```

`100644` is a normal file mode, `040000` a directory. Notice that a file’s *name* lives in the tree, not in the blob. Two files with identical content share one blob.

Step 3 — prove the hash is content-derived:

```bash
printf 'print("v2")\n' | git hash-object --stdin
git rev-parse HEAD:src/app.py
```

Both lines print the same id. Git did not “store the file under a name”; it stored content under its own hash and then referred to it from a tree.

Step 4 — look at the refs behind the names:

```bash
cat .git/HEAD
cat .git/refs/heads/main
git show-ref
```

Illustrative output:

```text
ref: refs/heads/main
8f3e1c0b2a4d6f8e0a1c3e5b7d9f1a2c4e6b8d0f
8f3e1c0b2a4d6f8e0a1c3e5b7d9f1a2c4e6b8d0f refs/heads/main
```

`HEAD` is a file containing the *name* of a branch; the branch is a file containing a commit id. “Moving a branch” is rewriting 41 bytes. That is why branches are cheap, and why a reset can be undone while the old commit still exists.

Step 5 — count what is stored and see unreachable objects:

```bash
git count-objects -v
git fsck --lost-found
```

`fsck` reports *dangling* commits or blobs that no ref reaches. Those are the objects the reflog can still point you to until garbage collection removes them.

**Check:** you should be able to say, without running anything, what object type each of `HEAD`, `HEAD^{tree}`, `HEAD:src` and `HEAD:src/app.py` names (commit, tree, tree, blob).

## Three places a change can live

| Place | What it is | Compare with |
| --- | --- | --- |
| Working tree | Files your editor shows | `git diff` (vs index) |
| Index (staging area) | Candidate next snapshot | `git diff --cached` (vs `HEAD`) |
| `HEAD` commit | Last committed snapshot on this branch | `git show HEAD` |

They can all differ at once. That is normal during careful work, not a bug.

**Mental model:** edit → stage the intentional slice → commit the slice → push when ready to share.

Inspect the index directly, because it is the least understood of the three:

```bash
git ls-files --stage
git diff --name-status HEAD
git status --short
```

Illustrative `git status --short` output:

```text
MM src/app.py
A  docs/guide.md
?? notes.txt
```

The two-character code is `XY`: **X** compares index to `HEAD`, **Y** compares working tree to index. `MM` means modified in both the index *and* afterwards in the working tree; `A ` means newly staged; `??` means untracked. Learn this table once and `--short` becomes the fastest status view.

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

Three dots (`A...B`) compare against the merge base. Two dots (`A..B`) compare the tips. Mixing them up produces confusing reviews. Note that `git log A..B` uses two dots to mean “commits reachable from B but not from A”, which is the review question most people actually want:

```bash
git log --oneline main..feature/timeout     # what the feature adds
git log --oneline feature/timeout..main     # what the feature is missing
```

**Detached HEAD** means `HEAD` points at a commit rather than a branch name. Commits made there can look “lost” when you switch away. Recover by naming them:

```bash
git switch -c rescue
```

### Fetch is not pull

`git fetch` updates your *remote-tracking* refs (`origin/main`) and touches nothing else. `git pull` is fetch followed by an integration step (merge by default, rebase if configured). Prefer fetching first so you can look before you integrate:

```bash
git fetch origin
git log --oneline --graph HEAD origin/main
git diff HEAD...origin/main
git pull --ff-only              # integrate only if no merge is needed
```

`--ff-only` refuses to create a surprise merge commit; if it fails, your branch and the remote have diverged and you must choose merge or rebase deliberately. Setting `git config --global pull.ff only` makes that the default.

## Four ways to integrate work

| Strategy | Resulting history | Use when | Watch out for |
| --- | --- | --- | --- |
| Merge commit | Both lines preserved; join commit has two parents | You want topology and original commits visible | Noisier `main` graph |
| Squash merge | One new commit on the target; branch commits are not ancestors | Small branches; tidy mainline | Harder to bisect inside the squash |
| Rebase | Your commits replayed on a new base as *new* commits | Cleaning a **private** branch before review | Rewrites commit ids; never rebase shared published history casually |
| Cherry-pick | One commit’s change copied elsewhere | Backporting a fix to a release branch | Duplicate change under a new id; later merges can conflict or double-apply |

There is no universally best strategy. Choose based on review style, backport needs, how builds trace to commits, and how quickly someone investigating an incident must read history.

A fast-forward is the degenerate case: if the target has not moved since you branched, “merging” just slides the pointer forward and creates no new commit. Use `git merge --no-ff` when you want a merge commit regardless, so the feature remains visible as a unit.

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

### Lab A: the same conflict, resolved by merge

Create a repository with a shared base and two diverging branches that edit the same line:

```bash
mkdir conflict-lab && cd conflict-lab && git init -b main
cat > config.yaml <<'EOF'
service: orders
timeout_seconds: 30
retries: 3
EOF
git add . && git commit -m "base config"

git switch -c feature/timeout
sed -i 's/timeout_seconds: 30/timeout_seconds: 10/' config.yaml
git commit -am "Lower timeout to 10s for fast failure"

git switch main
sed -i 's/timeout_seconds: 30/timeout_seconds: 60/' config.yaml
git commit -am "Raise timeout to 60s for slow upstream"
```

Merge and meet the conflict:

```bash
git merge feature/timeout
```

Illustrative output:

```text
Auto-merging config.yaml
CONFLICT (content): Merge conflict in config.yaml
Automatic merge failed; fix conflicts and then commit the result.
```

Open the file:

```text
service: orders
<<<<<<< HEAD
timeout_seconds: 60
=======
timeout_seconds: 10
>>>>>>> feature/timeout
retries: 3
```

Everything between `<<<<<<<` and `=======` is **ours** (the branch you are on, `main`); between `=======` and `>>>>>>>` is **theirs**. The markers are text in a file: tests, linters and YAML parsers will all choke on them, which is why a conflicted file must never be committed.

Before editing, gather intent with the three stages and a three-way view:

```bash
git diff --base config.yaml
git diff --ours config.yaml
git diff --theirs config.yaml
git log --merge --oneline -p -- config.yaml
```

`git log --merge` lists only the commits on each side that touched conflicted paths: it answers “who changed this and why?” in one command. In this lab one side wants fast failure and one wants tolerance for a slow upstream. Neither is wrong; the *real* resolution needs a human decision. Suppose you agree on separate settings:

```yaml
service: orders
connect_timeout_seconds: 10
read_timeout_seconds: 60
retries: 3
```

Finish the merge and verify:

```bash
git add config.yaml
git commit              # accept the prepared merge message
git log --graph --oneline --all
git ls-files -u         # must print nothing
grep -n '<<<<<<<\|>>>>>>>' config.yaml   # must print nothing
```

Illustrative graph:

```text
*   a91c3d7 (HEAD -> main) Merge branch 'feature/timeout'
|\
| * 5be0f12 (feature/timeout) Lower timeout to 10s for fast failure
* | c7d2e48 Raise timeout to 60s for slow upstream
|/
* 1f4a6b9 base config
```

The merge commit has two parents and *both original commits remain*. That is the merge strategy’s selling point.

### Lab B: the same conflict, resolved by rebase

Reset the lab to the state before merging (the reflog can find it, or start again), then:

```bash
git switch feature/timeout
git rebase main
```

Illustrative output:

```text
Auto-merging config.yaml
CONFLICT (content): Merge conflict in config.yaml
error: could not apply 5be0f12... Lower timeout to 10s for fast failure
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
```

Look at the file again. This time the markers read:

```text
<<<<<<< HEAD
timeout_seconds: 60
=======
timeout_seconds: 10
>>>>>>> 5be0f12 (Lower timeout to 10s for fast failure)
```

In a rebase, `HEAD` is the branch you are rebasing **onto** (so the “ours” side is `main`’s 60), and “theirs” is **your own commit being replayed**. That is the swap warned about earlier. Resolve to the same two-key form, then:

```bash
git add config.yaml
git rebase --continue
git log --graph --oneline --all
```

Illustrative graph:

```text
* e3a58c0 (HEAD -> feature/timeout) Lower timeout to 10s for fast failure
* c7d2e48 (main) Raise timeout to 60s for slow upstream
* 1f4a6b9 base config
```

The history is now **linear**: your commit sits on top of `main`, with a *new id* (`e3a58c0`, not `5be0f12`). If you had already pushed `feature/timeout`, the remote still has the old commit and a normal push will be rejected — you would need `--force-with-lease`, and everyone else who based work on the old commit would need to recover.

### Comparing the two outcomes

| Question | Merge result | Rebase result |
| --- | --- | --- |
| Original commit ids preserved? | Yes | No — replayed as new commits |
| Where is the conflict resolution recorded? | In the merge commit | Folded into the replayed commit |
| Shape of history | Branches and a join | Straight line |
| Safe on a branch others pulled? | Yes | No, unless the team agrees to rewrite |
| Conflicts to resolve for N commits | Once | Possibly once per replayed commit |
| `git revert` of the whole feature | `git revert -m 1 <merge>` | Revert each commit, or use a squash |

Neither is “cleaner” in the abstract. Pick by the question you expect to ask later: “what happened, in which order, by whom?” favours merge; “read it like a story” favours rebase.

### When a rebase goes wrong

| Symptom | Meaning | Action |
| --- | --- | --- |
| `You are currently rebasing branch ... onto ...` in `git status` | Rebase is paused for you | Resolve, `git add`, `git rebase --continue` |
| The same conflict repeats for every commit | Replayed commits touch the same lines | Consider `git rebase --abort` and squashing first |
| You resolved incorrectly and continued | Bad resolution is already in a replayed commit | `git reflog`, then `git reset --hard` to the `ORIG_HEAD` or the pre-rebase entry |
| Push rejected after rebase | Remote still holds old ids | `git push --force-with-lease` on a private branch only |

Before any rebase on work you care about, mark the starting point: `git branch backup/pre-rebase`. A branch is a 41-byte insurance policy.

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

Illustrative `git reflog | head`:

```text
2c8e4a1 (HEAD -> drill/recovery) HEAD@{0}: reset: moving to HEAD~1
9b3d7f5 HEAD@{1}: commit: drill: temporary commit
2c8e4a1 (HEAD -> drill/recovery) HEAD@{2}: checkout: moving from main to drill/recovery
```

`HEAD@{1}` is “where HEAD was one move ago”. You can use that notation directly: `git reset --hard HEAD@{1}` undoes the previous reset. Also remember `ORIG_HEAD`, which Git sets before risky operations such as merge, rebase and reset.

## Stash: parking uncommitted work

When you must change branches but are not ready to commit, **stash** shelves tracked changes:

```bash
git stash push -m "wip: health endpoint"
git stash list
git switch hotfix/login
# ... do the hotfix ...
git switch feature/add-health
git stash pop           # restore and drop the stash
```

By default stash ignores untracked files; add `-u` to include them. If `pop` conflicts, the stash is kept — it is dropped only after a clean apply. Prefer a short-lived WIP *branch* over a long-lived stash: stashes are unnamed, local and easy to forget.

## Tags: naming a release

A **tag** is a ref that does not move. Lightweight tags are bare names; **annotated** tags are objects with a tagger, date and message, so use them for releases:

```bash
git tag -a v1.4.0 -m "Release 1.4.0"
git show v1.4.0
git push origin v1.4.0          # tags are not pushed by plain git push
git describe --tags             # e.g. v1.4.0-12-g8d41b07
```

`git describe` output reads: nearest tag, number of commits since, and abbreviated commit id. Embedding it in a build is a cheap way to answer “which source produced this binary?”.

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

Illustrative result:

```text
5be0f12a9c3d7e1f4b6a8c0d2e4f6a8b0c2d4e6f is the first bad commit
commit 5be0f12a9c3d7e1f4b6a8c0d2e4f6a8b0c2d4e6f
Author: Sam Example <sam@example.com>
Date:   Tue Nov 11 10:12:44 2026 +0200

    Lower timeout to 10s for fast failure
```

For 1,000 commits, bisect needs about ten tests. Two practical notes: a squash-merged mainline gives you one large suspect commit, and a commit that does not build should be skipped (`git bisect skip`), not marked good or bad.

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

A review-ready self-check before you click “Create”:

| Check | Command or action |
| --- | --- |
| Is the diff only what I intend? | `git diff main...HEAD --stat` |
| Any secrets, debug output, stray files? | Read the full diff once, as a reviewer |
| Do commits tell a story? | `git log --oneline main..HEAD` |
| Does it build and pass tests from a clean checkout? | Run the project’s checks |
| Is the description enough for someone without context? | Purpose, scope, evidence, risk |

## Troubleshooting guide

| Symptom | Likely cause | First diagnostic | Safe resolution |
| --- | --- | --- | --- |
| `! [rejected] ... (non-fast-forward)` | Remote has commits you lack | `git fetch && git log HEAD..origin/<branch>` | Rebase (private) or merge; never bare `--force` |
| `Your branch and 'origin/main' have diverged` | Both sides moved | `git log --graph --oneline --all` | Choose merge or rebase deliberately |
| Merge keeps re-conflicting | Same lines changed repeatedly | `git log --merge -p` | Resolve once; consider `git rerere` (see Expert) |
| Branch “lost” its commits after a reset | Tip moved | `git reflog` | `git branch recovery <id>` |
| Revert of a merge fails with “is a merge but no -m option” | Merge has two parents | `git show --format=raw <sha>` | `git revert -m 1 <sha>` (see Expert) |
| Cherry-pick conflicts | Context differs on target branch | `git status`, stages `:1:`–`:3:` | Resolve, `git cherry-pick --continue` |
| `HEAD detached at <sha>` after checking out a tag | Tags are not branches | `git branch --show-current` prints nothing | `git switch -c <name>` if you will commit |
| Diff looks huge but change was small | Whitespace or line-ending churn | `git diff -w --stat` | Normalise with `.gitattributes`; commit formatting separately |

## Knowledge consolidation

- Commits are nodes in a **directed graph**; branches are movable labels.
- Know which of **working tree / index / HEAD** you are changing.
- Prefer **revert** on shared history; reserve **reset --hard** for private recovery.
- Conflicts are about **intent**; stages beat folklore about “ours/theirs”.
- The reflog rescues *local* mistakes; it is not organisational backup.
- Merge preserves ids and topology; rebase rewrites ids to give a line. Choose by the question you expect to ask later.
- Fetch first, look, then integrate; `--ff-only` makes surprises loud.
- Name your starting point (a backup branch or tag) before any risky operation.

## Exercises

**Exercise 1.** Using two clones of one repository, make conflicting edits to the same line on two branches, merge, and resolve by documenting each side’s intent before editing. Abort once with `git merge --abort`, then repeat and finish the merge.

**Exercise 2 (challenge).** On a disposable branch, create three commits, `reset --hard` to drop them from the tip, recover them via reflog onto a new branch, then on a *pushed* branch use `git revert` (not reset) to undo a different commit and explain why the strategies differed.

**Exercise 3 — Object walk.** In a fresh repository with two commits, print the commit, its tree, a subtree and a blob using only `git cat-file`. Then change one character in one file, commit, and list which object ids changed (commit, root tree, the subtree on the path, one blob) and which did **not** (every other blob). Explain why this makes snapshots cheap.

**Exercise 4 — Merge versus rebase.** Repeat Lab A and Lab B on fresh copies. Draw both graphs, record which commit ids changed, and write two sentences stating which you would choose for (a) a two-day feature branch reviewed by a team and (b) a one-week hotfix backported to a release branch.

**Exercise 5 — Bisect it.** Write a 20-commit history in which a script `check.sh` starts failing at commit 13. Run `git bisect run ./check.sh` and confirm it names commit 13. Then make commit 9 unbuildable and use `git bisect skip` to show how the result changes.

**Exercise 6 — Fetch discipline.** Clone a repository twice. In clone B, push a commit. In clone A, create a local commit and run `git fetch`, then compare with `git log --oneline --graph --all`, then `git pull --ff-only` and read the failure. Resolve it first by merge, then again by rebase.

**Solution notes.** Conflict markers must disappear before commit; `git ls-files -u` should be empty when you are done. After hard reset, `git reflog` should still show the lost tip for a time. Revert creates a forward commit; history still contains the original change plus its undo.

**Solution notes (Exercise 3).** Changing one character changes one blob, every tree on the path from that blob to the root, and the commit. All untouched blobs and trees keep their ids and are shared between commits.

**Solution notes (Exercise 4).** Merge keeps the original commit ids; rebase replays them with new ids and a linear shape. A reasonable answer: (a) rebase privately before review and then stop rewriting, or merge if the team values topology; (b) cherry-pick with `-x` for the backport, because merging a whole branch onto a release line carries unwanted changes.

**Solution notes (Exercise 5).** `git bisect run` should name commit 13 as the first bad commit. When commit 9 is skipped, bisect still converges as long as a good commit remains on the far side; if the first bad commit is adjacent to skipped ones, Git reports a set of candidates instead of one.

**Solution notes (Exercise 6).** `--ff-only` fails because histories diverged. Merge adds a join commit; rebase replays your local commit on top of the remote one. Both leave the same file content if resolved identically.
