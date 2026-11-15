# T-DEV-01-B — Beginner Foundations

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-b"></a>
#### T-DEV-01-B — Beginner Foundations

## Why this matters

Imagine you have been editing a project for weeks. You improve one file, break another, try a fix, then decide the previous version was better — but you cannot remember what the previous version was. Or a colleague changes the same file as you and both of you email copies named `final_v2_really_final.docx`. Version control exists to solve that class of problem: it records *what changed*, *when*, *by whom*, and *why*, so you can move forward without losing the ability to go back.

Git is the most widely used system for that job in software. Hosting platforms such as GitHub, GitLab and Bitbucket store a copy of a Git repository and add collaboration features (permissions, reviews, discussions). Git itself is the tool on your computer that records history. You need both ideas: local history, and a shared remote copy.

This Beginner section assumes you can open a terminal (a text window where you type commands) and create folders. It does **not** assume you have used Git before.

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

## Guided example: from an empty folder to a shared repository

Work in a disposable directory outside any real production project. Commands below use a fictional service called `orders-platform`.

### 1. Create the folder and turn it into a repository

```bash
mkdir orders-platform && cd orders-platform
git init -b main
```

What this does:

- `mkdir` creates an empty project folder.
- `git init -b main` creates the hidden `.git` directory and starts you on a branch named `main`.

Observable check:

```bash
ls -a          # you should see .git
git status     # "No commits yet" / empty tree message
```

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

Expect every new file to be **untracked**. Staging marks what belongs in the next snapshot:

```bash
git add README.md .gitignore .env.example app infra deploy docs
git status
git diff --cached --stat
```

`git diff --cached` shows what *will* be in the commit. Then record it:

```bash
git commit -m "Initial repository layout, README and ignore rules"
git log --oneline
```

You should see one commit with a short hash and your message. That hash is the commit’s identity.

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

## Three states every beginner must distinguish

| State | Meaning | Typical `git status` hint |
| --- | --- | --- |
| Tracked | Git knows the file and records changes to it | listed under changes not staged / to be committed |
| Untracked | Git has never been told to remember the file | listed under “Untracked files” |
| Ignored | Matched by `.gitignore`; Git will not suggest adding it | omitted from status unless you force it |

Ignoring does **not** remove a file already in history. Committing a secret and then adding it to `.gitignore` leaves the secret in older commits.

## Everyday loop (memorise the intent, not only the keys)

1. Update your view of the shared default branch (`git switch main` then `git pull` when you work with a remote).
2. Create a short-lived branch for one purpose.
3. Edit files.
4. `git status` and `git diff` — understand the change.
5. `git add` the files that belong together.
6. `git commit` with a message that will make sense in six months.
7. `git push` and open a pull request.

## Common mistakes and how they look

| Mistake | Symptom | Recovery idea |
| --- | --- | --- |
| Committing `.env` with a real password | Secret appears in `git log -p` | Rotate the secret first; treating history rewrite as a later incident step |
| Huge unrelated `git add .` | Commit mixes docs, secrets and experiments | Reset the commit if not pushed (`git reset --soft HEAD~1`) and restage carefully |
| Editing directly on `main` | Hard to review; risky for teams | Create a branch immediately; move commits with care |
| Confusing local success with host acceptance | `commit` works, `push` rejected | Read the host message; often branch protection |
| Expecting empty folders to appear in Git | Folder missing after clone | Add a placeholder file |

## Knowledge consolidation

- Git records **snapshots** (commits), not a mysterious undo stack.
- The **index** is the deliberate “what goes into the next snapshot”.
- A **branch** is a name for a commit line of work, not a second copy of the disk.
- **Local history** and **host rules** are different systems.
- **Ignore early**; never rely on ignore rules to erase a committed secret.

## Exercises

**Exercise 1 — Guided self-check.** Create the layout above, make two branches that each change one different file, and run `git log --oneline --graph --all` before and after merging one branch into `main` (locally with `git switch main && git merge <branch>`). Write one sentence for what `git status` reported after each major step.

**Exercise 2 — Transfer.** Without looking at the commands above, explain to a colleague the difference between `git status`, `git diff` and `git diff --cached`, then demonstrate all three on a throwaway repository.

**Solution notes (Exercise 1).** Before any merge you should see two diverging lines on the graph. After merging one feature branch into `main`, that branch’s commit should be reachable from `main`. `git status` on a clean branch tip should report a clean working tree. If you still see untracked files, you created something you never added — that is normal and not an error until you decide whether it belongs in history.
