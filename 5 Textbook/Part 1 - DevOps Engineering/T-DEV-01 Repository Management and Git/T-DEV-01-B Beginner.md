# T-DEV-01-B — Beginner Foundations

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-b"></a>
#### T-DEV-01-B — Beginner Foundations

**Core vocabulary**

| Term | Meaning |
| --- | --- |
| Repository | A versioned collection of files together with their full history. |
| Commit | A recorded snapshot of the tracked files, with an author, message and parent commit. |
| Branch | A movable name that points at a commit. It is not a copy of the project. |
| Remote | A named destination for fetching and pushing history (conventionally `origin`). |
| Pull request / merge request | A review workflow provided by a hosting platform (GitHub, GitLab). It is not a Git object. |
| Default branch | The main integration branch, usually `main`. |

**Local Git and the hosting platform are different systems.** Git keeps history on your machine. A host adds a copy plus collaboration features: permissions, reviews, checks and branch rules. Many surprises come from forgetting that a rule enforced by the host is invisible to local Git until a push is rejected.

**Your first repository**

```bash
mkdir orders-platform && cd orders-platform
git init -b main
mkdir -p app infra deploy docs/decisions
printf '# orders-platform\n' > README.md
printf '# Application\n'     > app/README.md
printf '# Infrastructure\n'  > infra/README.md
git status                 # new files are "untracked"
git add .
git commit -m "Initial repository layout"
git log --oneline
```

Git tracks files, not folders, which is why each directory contains a small README. `git status` shows untracked files until you stage them with `git add`; a commit records what is staged.

**The everyday loop**

```bash
git switch -c docs/add-onboarding      # create a branch for one purpose
# ... edit files ...
git status && git diff                 # what changed?
git add CONTRIBUTING.md
git commit -m "Add contributor guide"
git push -u origin docs/add-onboarding # -u sets upstream tracking
```

Then open a pull request in the hosting UI. A useful description states the purpose, the scope, the evidence that it works, the risk and who should review.

**Three things that are not the same**

- *Tracked*: Git records changes to the file.
- *Untracked*: Git has not been told about the file.
- *Ignored*: matched by `.gitignore`, so Git will not suggest adding it. Ignoring does not remove anything already committed and does not protect a secret.

**Basic hygiene.** Create a `.gitignore` before the first real commit. Ignore local configuration and credentials (`.env`), dependency and build output (`node_modules/`, `__pycache__/`, `dist/`), Terraform local state (`*.tfstate`, `.terraform/`) and editor noise. Commit a safe template such as `.env.example` instead of the real file.

**Exercise.** Create the layout above, make two branches that each change one file, and compare `git log --oneline --graph --all` before and after merging one of them. Write down in one sentence what `git status` told you at each step.
