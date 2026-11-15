# T-DEV-01-B — Beginner Foundations

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-b"></a>
#### T-DEV-01-B — Beginner Foundations

## Why this matters

Imagine you have been editing a project for weeks. You improve one file, break another, try a fix, then decide the previous version was better — but you cannot remember what the previous version was. Or a colleague changes the same file as you and both of you email copies named `final_v2_really_final.docx`. Version control exists to solve that class of problem: it records *what changed*, *when*, *by whom*, and *why*, so you can move forward without losing the ability to go back.

Git is the most widely used system for that job in software. Hosting platforms such as GitHub, GitLab and Bitbucket store a copy of a Git repository and add collaboration features (permissions, reviews, discussions). Git itself is the tool on your computer that records history. You need both ideas: local history, and a shared remote copy.

This Beginner section assumes you can open a terminal (a text window where you type commands) and create folders. It does **not** assume you have used Git before. Every command uses a fictional service called `orders-platform`; nothing here depends on any other course material. Where an output is shown, it is labelled *illustrative*: your hashes, dates and wording will differ slightly by Git version, but the *shape* will match.

## First principles: a file is not a version

A file on disk is the *current* content. A *version* is a remembered snapshot of content at a point in time. Without version control, “remembering” usually means copying files by hand. With Git, remembering is a deliberate recorded action called a **commit**.

Analogy (and its limit): a commit is like saving a checkpoint in a game. The analogy fails because Git checkpoints are *named*, *linked* to earlier checkpoints, and *shared* with other people — not just private undo.

| Everyday idea | Git idea |
| --- | --- |
| Project folder | Working tree (your files as the editor sees them) |
| “I am ready to remember this” | Stage the relevant files, then commit |
| Checkpoint with a note | Commit with a message |
| Named line of work | Branch |
| Shared backup / collaboration copy | Remote (often called `origin`) |

## Local Git versus the hosting platform

**Local Git** keeps history in a hidden directory named `.git` inside your project. Commands such as `git commit` only change that local history until you push.

**A hosting platform** holds another copy of that history and adds:

- accounts and permissions
- pull requests / merge requests (review workflows)
- branch protection rules
- issue trackers and CI integrations

A rule on the host (for example “no direct pushes to `main`”) is invisible to local Git until you try to push and the host rejects you. Many beginners think Git “broke” when the host enforced a policy. It did not: two systems disagreed.

A useful habit when something fails is to ask first: *which system said no?* If the message begins with `error: failed to push some refs` and quotes a URL, the remote host answered. If it begins with `fatal:` or `error:` and names a local file or state, local Git answered.

## Core vocabulary in context

| Term | Meaning in practice |
| --- | --- |
| Repository | A project’s files *plus* their full recorded history (the `.git` directory makes a folder a repository). |
| Working tree | The files you see and edit. |
| Index / staging area | The set of changes you have marked for the *next* commit. |
| Commit | An immutable snapshot of the staged files, with author, message and parent commit(s). |
| Branch | A movable name that points at a commit. Creating a branch does **not** copy the whole project. |
| `HEAD` | “Where you are now” — usually the tip of the current branch. |
| Remote | A named URL of another copy of the repository (conventionally `origin`). |
| Clone | A full local copy of a remote repository, including history. |
| Pull request / merge request | A hosting-platform review of proposed commits; not a Git object itself. |
| Default branch | The main integration branch, usually `main`. |

## Installing and identifying yourself

Install Git from your operating system’s package manager or from the official Git site, then check it:

```bash
git --version
```

You should see a version number. Then set your identity for commits on this machine (use a no-reply address if you prefer privacy):

```bash
git config --global user.name "Your Name"
git config --global user.email "you@users.noreply.github.com"
git config --global init.defaultBranch main
```

`--global` writes to your user config. These values are embedded in every commit you create on this machine until you change them. They are *labels*, not authentication: the host still decides who may push.

### Three configuration levels, and which one wins

Git reads configuration from three places and the **most specific wins**:

| Level | Flag | Typical file | Applies to |
| --- | --- | --- | --- |
| System | `--system` | `/etc/gitconfig` | Every user on the machine |
| Global (user) | `--global` | `~/.gitconfig` or `~/.config/git/config` | Every repository you use |
| Local (repository) | `--local` (default inside a repo) | `.git/config` | Only this repository |

A local `user.email` overrides the global one. That is useful (a work address in a work repository) and also the classic source of confusion (a personal address on a work commit because you cloned onto a laptop that only had global settings, or the reverse).

Always ask Git where a value came from rather than guessing:

```bash
git config --list --show-origin | grep -E 'user\.(name|email)'
git config --show-origin user.email
git config --show-scope --get-all user.email
```

Illustrative output:

```text
file:/home/sam/.gitconfig	user.email=sam@users.noreply.github.com
file:.git/config	user.email=sam.work@example.com
```

Two lines mean two levels defined it; the later (more local) line wins. The `--show-origin` flag tells you which file to edit.

### Identity and configuration pitfalls

| Symptom | Likely cause | Check | Fix |
| --- | --- | --- | --- |
| `Author identity unknown` / `fatal: unable to auto-detect email address` on first commit | No `user.name` / `user.email` set anywhere | `git config user.email` prints nothing | Set them with `git config --global ...` |
| Commits show as an unknown grey avatar on the host | Commit email not attached to your host account | `git log -1 --format='%an <%ae>'` | Add that email to your host account, or change `user.email` and use a no-reply address |
| Work commits carry a personal email | Only a global identity exists | `git config --show-origin user.email` | Set a local identity in the work repository, or use conditional includes (below) |
| `git push` asks for a password every time | HTTPS without a credential helper | `git config credential.helper` | Configure a helper or switch to SSH keys |

Changing `user.email` afterwards does **not** rewrite commits you already made. Commit identity is part of the commit’s content and hash. If you published a commit with the wrong email, the practical choice for a beginner is: fix the setting going forward and accept the old commit.

**Conditional identity.** For a shared machine, an `[includeIf "gitdir:~/work/"]` block in `~/.gitconfig` can load a work-specific file for every repository under that directory (the trailing slash matters).

**Credentials are separate from identity.** `user.name` and `user.email` are labels stamped into commits. To *prove who you are* to a host you need an SSH key pair or an HTTPS token, ideally narrowly scoped, stored by a credential helper — never pasted into a file in the repository or a command you will keep in shell history.

## Guided example: from an empty folder to a shared repository

Work in a disposable directory outside any real production project. Commands below use a fictional service called `orders-platform`.

### 1. Create the folder and turn it into a repository

```bash
mkdir orders-platform && cd orders-platform
git init -b main
```

What this does: `mkdir` creates the folder; `git init -b main` creates the hidden `.git` directory and starts on `main`.

Observable check:

```bash
ls -a          # you should see .git
git status     # "No commits yet" / empty tree message
```

Illustrative output of the second command:

```text
On branch main

No commits yet

nothing to commit (create/copy files and use "git add" to track)
```

Read it: you are on `main`; the branch points at nothing yet; there is nothing for Git to notice.

### 2. Create a small, intentional layout

Git tracks **files**, not empty folders. A common pattern is a tiny README in each folder so the structure is stored:

```bash
mkdir -p app infra deploy docs/decisions
printf '# orders-platform\n\nSample service used in textbook examples.\n' > README.md
printf '# Application\n'     > app/README.md
printf '# Infrastructure\n'  > infra/README.md
printf '# Deployment\n'      > deploy/README.md
printf '# Decisions\n'       > docs/decisions/README.md
```

### 3. Ignore secrets and noise *before* the first real commit

Create `.gitignore` early. Ignoring a file only affects *future* suggestions to add it; it does not scrub a secret already committed.

```bash
cat > .gitignore <<'EOF'
.env
.env.*
!.env.example
*.pem
*.key
.venv/
__pycache__/
node_modules/
dist/
.terraform/
*.tfstate
*.tfstate.*
.DS_Store
EOF
printf 'DATABASE_URL=postgres://user:change-me@localhost:5432/orders\n' > .env.example
```

### 4. Inspect, stage and commit

```bash
git status
```

Expect every new file to be **untracked**. Illustrative output:

```text
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.env.example
	.gitignore
	README.md
	app/
	deploy/
	docs/
	infra/

nothing added to commit but untracked files present (use "git add" to track)
```

Note what is **not** listed: nothing matching `.gitignore` appears, and that is deliberate. Staging marks what belongs in the next snapshot:

```bash
git add README.md .gitignore .env.example app infra deploy docs
git status
git diff --cached --stat
```

Illustrative output of `git diff --cached --stat`:

```text
 .env.example             | 1 +
 .gitignore               | 13 +++++++++++++
 README.md                | 3 +++
 app/README.md            | 1 +
 deploy/README.md         | 1 +
 docs/decisions/README.md | 1 +
 infra/README.md          | 1 +
 7 files changed, 21 insertions(+)
```

`git diff --cached` shows what *will* be in the commit. Then record it:

```bash
git commit -m "Initial repository layout, README and ignore rules"
git log --oneline
```

You should see one commit with a short hash and your message. That hash is the commit’s identity.

```text
3f9a1c2 Initial repository layout, README and ignore rules
```

### 5. Make a branch for one purpose

Do not pile unrelated edits onto `main` without a habit. Create a branch for a single change:

```bash
git switch -c docs/add-contributing
printf '# Contributing\n\n1. Create a branch\n2. Open a pull request\n' > CONTRIBUTING.md
git status
git diff
git add CONTRIBUTING.md
git commit -m "Add contributor guide"
```

`git switch -c` creates and checks out the branch. `git diff` (without `--cached`) shows unstaged edits; after `git add`, use `git diff --cached` again if you want to review the staged patch.

Notice that `git diff` printed nothing for `CONTRIBUTING.md` before you added it. Plain `git diff` ignores **untracked** files entirely, because Git has no earlier version to compare against. This surprises many beginners; the cure is `git status` first, always.

### 6. Add a remote and push

Create an empty private repository on your host (do not let the host add a README if you already have local commits — that creates divergent histories). Then:

```bash
git remote add origin git@github.com:<your-user>/orders-platform.git
# HTTPS alternative:
# git remote add origin https://github.com/<your-user>/orders-platform.git

git push -u origin main
git push -u origin docs/add-contributing
```

`-u` sets upstream tracking so later `git push` / `git pull` know which remote branch to use.

On the hosting site, open a **pull request** from `docs/add-contributing` into `main`. A useful description states: purpose, what changed, how you checked it, risk, and who should review.

Verify what you configured with `git remote -v` and `git branch -vv`. In the latter, `[origin/main: ahead 1]` means one local commit is unpushed and `behind 2` means the remote has two you have not fetched.

## Reading `git status` and `git diff` like a professional

Reading output accurately is the single biggest beginner accelerator. Make a small edit and a new file in the example repository, stage one of them, and look at all three views.

```bash
printf '\nRun the tests before opening a pull request.\n' >> CONTRIBUTING.md
printf 'TODO\n' > notes.txt
git add CONTRIBUTING.md
printf 'Ask a colleague to review.\n' >> CONTRIBUTING.md
git status
```

Illustrative output:

```text
On branch docs/add-contributing
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	modified:   CONTRIBUTING.md

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   CONTRIBUTING.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	notes.txt
```

`CONTRIBUTING.md` appears **twice**. That is correct, not a bug: you staged the first edit, then made a second edit afterwards. The index holds version one of your change; the working tree holds version two. Git is showing three populations at once:

| Section in status | Meaning | Compare with |
| --- | --- | --- |
| Changes to be committed | Index differs from last commit | `git diff --cached` |
| Changes not staged for commit | Working tree differs from index | `git diff` |
| Untracked files | Never added; invisible to `git diff` | Decide: add, ignore or delete |

Now look at the second view:

```bash
git diff
```

Illustrative output, annotated:

```diff
diff --git a/CONTRIBUTING.md b/CONTRIBUTING.md
index 5b3c1d2..9e0a7f4 100644
--- a/CONTRIBUTING.md
+++ b/CONTRIBUTING.md
@@ -4,3 +4,4 @@
 2. Open a pull request
 
 Run the tests before opening a pull request.
+Ask a colleague to review.
```

How to read it:

- `a/` is the *old* side (here, the index) and `b/` is the *new* side (here, the working tree). They are labels, not directories.
- `index 5b3c1d2..9e0a7f4` shows abbreviated blob ids for the two versions of the file.
- `--- a/` and `+++ b/` name the two sides.
- `@@ -4,3 +4,4 @@` means: starting at line 4, the old side showed 3 lines and the new side shows 4. Treat it as a location marker.
- Lines starting with a space are unchanged context; `+` is added; `-` is removed.

`git diff --cached` would show only the *first* edit. If you commit now, the second edit stays in the working tree — that is how you split one session into two clean commits.

To pick *parts* of a file, use patch mode and answer each question:

```bash
git add -p CONTRIBUTING.md
```

Press `y` to stage a hunk, `n` to skip it, `s` to split a hunk into smaller pieces, `q` to quit. Patch mode is the beginner’s best tool for turning a messy session into reviewable commits.

## Ignore rules: how `.gitignore` actually works

`.gitignore` is a list of **patterns**, one per line, matched against paths relative to the file’s own directory. The mechanics are simple but have sharp edges.

| Pattern | Matches | Notes |
| --- | --- | --- |
| `*.log` | Any file ending `.log`, in any directory | A pattern with no slash matches at every level |
| `/build` | Only a `build` entry at the repository root | A leading slash anchors the pattern |
| `build/` | A directory named `build` at any level | A trailing slash restricts to directories |
| `docs/*.tmp` | `.tmp` files directly inside `docs/` | A slash inside the pattern anchors it to this directory |
| `**/cache` | A `cache` entry at any depth | `**` matches across directory levels |
| `!keep.log` | Re-includes `keep.log` | Negation; see the parent-directory trap below |
| `# note` | Nothing | A comment line |

**Order matters.** Later lines override earlier ones, which is why `.env.*` comes *before* `!.env.example`; reverse them and `.env.example` is ignored again.

**The parent-directory trap.** Git cannot re-include a file if a parent directory is itself excluded. This does **not** work:

```text
logs/
!logs/keep.txt
```

Because `logs/` excludes the whole directory, Git never looks inside it. The working form ignores the *contents* and then re-includes one:

```text
logs/*
!logs/keep.txt
```

**Ignore rules only affect untracked files.** If a file is already tracked, adding it to `.gitignore` changes nothing: Git continues to record its edits. That is the usual cause of “I ignored it but it still shows as modified.” To stop tracking while keeping the file on disk:

```bash
git rm --cached config/local.yaml
git commit -m "Stop tracking local config"
```

`--cached` removes it from the index but leaves your working copy alone. This stops *future* tracking; the file remains in past commits.

**Where else rules can live.** Not every ignore belongs in the shared `.gitignore`:

| Location | Scope | Use for |
| --- | --- | --- |
| `.gitignore` in the repository | Shared with everyone who clones | Build outputs, dependency folders, secrets patterns the project always produces |
| `.git/info/exclude` | Only your clone, never committed | Personal scratch files specific to this project |
| Global excludes file (`core.excludesFile`) | All your repositories | Editor or OS noise such as `.DS_Store`, `*.swp`, `.idea/` |

```bash
git config --global core.excludesFile ~/.gitignore_global
printf '.DS_Store\n*.swp\n.idea/\n.vscode/\n' > ~/.gitignore_global
```

**Debugging an ignore rule.** When you cannot tell why a file is or is not ignored, ask Git:

```bash
git check-ignore -v build/output.js
git status --ignored
git ls-files --others --ignored --exclude-standard
```

Illustrative output of `check-ignore -v`:

```text
.gitignore:8:dist/	dist/bundle.js
```

That reads: file `.gitignore`, line 8, pattern `dist/`, matched the path. If the command prints nothing and exits non-zero, no rule matches. Forcing an ignored file into the repository is possible with `git add -f`; treat that as a deliberate, rare decision, not a convenience.

**Ignore is hygiene, not security.** Rules prevent accidents; they do not stop `git add -f`, do not protect a secret committed before the rule existed, and do not apply on the host.

## Three states every beginner must distinguish

| State | Meaning | Typical `git status` hint |
| --- | --- | --- |
| Tracked | Git knows the file and records changes to it | listed under changes not staged / to be committed |
| Untracked | Git has never been told to remember the file | listed under “Untracked files” |
| Ignored | Matched by `.gitignore`; Git will not suggest adding it | omitted from status unless you force it |

Ignoring does **not** remove a file already in history. Committing a secret and then adding it to `.gitignore` leaves the secret in older commits.

## Writing a commit message someone can use

A commit message is a note to a future reader — possibly you during an incident. Use an imperative first line (“Add…”), a blank line, then a body explaining **why**:

```text
Add retry limit to payment client

The client retried indefinitely when the gateway returned 503,
holding worker threads. Cap retries at 3 with exponential backoff.

Refs: ORD-142
```

- A body that explains **why**, not a replay of the diff, and a tracker reference if you have one.

Poor messages (`fix`, `wip`, `Update file.py`) cost the reader time because they restate the diff or carry no intent; they are tolerable on a private branch and unacceptable in shared history.

## Everyday loop (memorise the intent, not only the keys)

1. Update your view of the shared default branch (`git switch main` then `git pull` when you work with a remote).
2. Create a short-lived branch for one purpose.
3. Edit files.
4. `git status` and `git diff` — understand the change.
5. `git add` the files that belong together.
6. `git commit` with a message that will make sense in six months.
7. `git push` and open a pull request.

## Undoing small mistakes safely

Learn these exits; all are safe for **unpushed** work:

| Situation | Command | Effect |
| --- | --- | --- |
| Staged the wrong file | `git restore --staged <file>` | Removes from the index; file edits remain |
| Want to throw away edits to a tracked file | `git restore <file>` | Working tree reverts to the index (edits are **lost**) |
| Committed too early; want to re-stage | `git reset --soft HEAD~1` | Commit undone; changes stay staged |
| Message typo in the last, unpushed commit | `git commit --amend` | Replaces the last commit with a new one |

`git restore <file>` has no undo: Git never recorded those unstaged edits.

## Common mistakes and how they look

| Mistake | Symptom | Recovery idea |
| --- | --- | --- |
| Committing `.env` with a real password | Secret appears in `git log -p` | Rotate the secret first; treat history rewrite as a later incident step |
| Huge unrelated `git add .` | Commit mixes docs, secrets and experiments | Reset the commit if not pushed (`git reset --soft HEAD~1`) and restage carefully |
| Editing directly on `main` | Hard to review; risky for teams | Create a branch immediately; move commits with care |
| Confusing local success with host acceptance | `commit` works, `push` rejected | Read the host message; often branch protection |
| Running Git commands outside a repository | `fatal: not a git repository (or any of the parent directories): .git` | `cd` into the project, or run `git init` if it is meant to be new |

## Troubleshooting: messages you will meet in week one

**`error: failed to push some refs ... hint: Updates were rejected because the remote contains work that you do not have locally`.** Someone (or the host’s “add a README” checkbox) created a commit your clone has not seen. Run `git fetch`, look with `git log --oneline --graph --all`, then integrate with `git pull --rebase` (private branch) or `git pull` (merge). Do **not** reach for `--force`.

**`fatal: refusing to merge unrelated histories`.** Two repositories were created independently — typically a local `git init` plus a host-side repository that already has an initial commit. Decide which history is authoritative. If the host repository is empty except for a README you do not need, delete and recreate it empty. If you must join them, the explicit (and deliberate) form is `git pull origin main --allow-unrelated-histories`.

**`remote: Permission to <repo> denied` / `Permission denied (publickey)`.** Authentication failed — the host does not know your key or token. Check `git remote -v` for the exact URL, test the SSH connection (`ssh -T git@github.com`), and confirm the key is added to your account. Authentication failure is not a Git bug.

**`You are in 'detached HEAD' state.`** You checked out a commit, tag or remote branch directly. Reading is safe. If you want to keep new commits, name them first with `git switch -c <name>`.

**`error: Your local changes to the following files would be overwritten by checkout`.** Switching branches would destroy uncommitted edits. Either commit them, or stash them temporarily with `git stash push -m "wip"` and restore with `git stash pop`.

**A file still shows as modified after I added it to `.gitignore`.** It is already tracked; see `git rm --cached` above.

## Knowledge consolidation

- Git records **snapshots** (commits), not a mysterious undo stack.
- The **index** is the deliberate “what goes into the next snapshot”.
- A **branch** is a name for a commit line of work, not a second copy of the disk.
- **Local history** and **host rules** are different systems.
- **Ignore early**; never rely on ignore rules to erase a committed secret.
- Identity is a **label**, resolved from system, global and local config — ask `--show-origin`.
- `git status` showing a file twice is normal; it means the index and the working tree disagree.
- A good message explains **why**; the diff already shows what.
- Name the system that said no (local Git or the host) before you try a fix.

## Exercises

**Exercise 1 — Guided self-check.** Create the layout above, make two branches that each change one different file, and run `git log --oneline --graph --all` before and after merging one branch into `main` (locally with `git switch main && git merge <branch>`). Write one sentence for what `git status` reported after each major step.

**Exercise 2 — Transfer.** Without looking at the commands above, explain to a colleague the difference between `git status`, `git diff` and `git diff --cached`, then demonstrate all three on a throwaway repository.

**Exercise 3 — Identity audit.** In a throwaway repository, set a *local* `user.email` that differs from your global one. Make a commit and run `git log -1 --format='%an <%ae>'`. Then run `git config --show-origin user.email` and explain which file supplied the value. Finally, remove the local setting with `git config --unset user.email` and confirm the global value takes over.

**Exercise 4 — Ignore detective.** Create `logs/app.log` and `logs/keep.txt`. First write `logs/` and `!logs/keep.txt` in `.gitignore` and run `git status`; then change the first line to `logs/*` and run it again. Use `git check-ignore -v logs/keep.txt` both times. Explain the difference in your own words.

**Solution notes (Exercise 1).** Before any merge you should see two diverging lines on the graph. After merging one feature branch into `main`, that branch’s commit should be reachable from `main`. `git status` on a clean branch tip should report a clean working tree. If you still see untracked files, you created something you never added — that is normal and not an error until you decide whether it belongs in history.

**Solution notes (Exercise 3).** The value comes from `.git/config` while the override exists, then from your global file. Existing commits keep their original email.

**Solution notes (Exercise 4).** `logs/` excludes the directory wholesale, so `keep.txt` stays ignored; `logs/*` excludes contents individually, so the negation wins.
