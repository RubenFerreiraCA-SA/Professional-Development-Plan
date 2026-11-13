# D01 — Git & Repository Foundations

**Estimated study time:** 8–10 hours  
**DevOps syllabus weighting:** 7%  
**Prerequisites:** Git installed, a terminal and an account on GitHub or GitLab. Basic command-line familiarity is helpful.

## Objective

Build a **secure, reviewable Git repository** that becomes the foundation of the continuous practical project used throughout the [DevOps syllabus](DevOps_Syllabus.md). You will work with Git locally, authenticate to a remote repository, protect the main branch and merge a change through a pull or merge request.

## Learning outcomes

On completion, you should be able to:

1. Explain repositories, commits, branches, remotes and the differences between working tree, staging area and commit history.
2. Configure Git identity and secure SSH authentication to a remote host.
3. Structure a repository with separate application, infrastructure and deployment directories.
4. Exclude credentials and generated files using `.gitignore` and recognise that ignoring a file does not remove it from existing history.
5. Create feature branches, make readable commits, open and review a pull/merge request, and merge without bypassing repository rules.
6. Demonstrate that the default branch is protected and the remote history reflects the reviewed changes.

## Suggested learning plan

| Activity | Estimated time | Outcome |
| --- | ---: | --- |
| Git fundamentals and local practice | 1.5–2 hours | Understand and inspect repository history |
| Identity and SSH authentication | 1–1.5 hours | Authenticated remote access |
| Repository structure and ignore rules | 1–1.5 hours | Clean, safe capstone repository |
| Branching and pull/merge requests | 2–2.5 hours | Reviewed, merged feature |
| Branch protection, verification and evidence | 1.5–2.5 hours | Demonstrable, repeatable workflow |
| **Total** | **8–10 hours** | |

These are estimates, not deadlines. Familiar users can move faster; newcomers may need more practice.

## 1. Git fundamentals

Learn the purpose of each part of the workflow:

| Concept | What to know |
| --- | --- |
| Working tree | Files currently being edited |
| Staging area | Changes selected for the next commit |
| Commit | A recorded snapshot with a message and parent history |
| Branch | A movable pointer to a sequence of commits |
| Remote | A named connection to a repository hosted elsewhere |
| Pull/merge request | A proposed change that can be inspected and reviewed before merging |

**Practice in a disposable local repository:**

```bash
mkdir git-practice && cd git-practice
git init -b main
git status
echo "# Git Practice" > README.md
git add README.md
git commit -m "docs: initialise practice repository"
git log --oneline --decorate
git switch -c practice/readme-update
echo "Learning Git fundamentals." >> README.md
git diff
git add README.md
git diff --cached
git commit -m "docs: expand practice readme"
git log --oneline --graph --all
```

If Git requests your identity, complete the next section and retry the commit. Use `git status` before and after staging to explain what changed.

## 2. Git identity and SSH authentication

Configure an identity that you want attached to your commits:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global --list
```

For SSH, **check for an existing key before creating another**. If you need a new key, use an Ed25519 key with a passphrase:

```bash
ssh-keygen -t ed25519 -C "you@example.com"
```

Add the **public** key (`.pub` file) to your Git hosting account. Follow your operating system's instructions to load the private key into the SSH agent, then test authentication:

```bash
ssh -T git@github.com
# Or, for GitLab:
ssh -T git@gitlab.com
```

A successful authentication test does not necessarily grant access to every repository. **Never upload, paste or commit your private SSH key.**

## 3. Create the capstone repository

Create a new remote repository for the ongoing application delivery project, then clone it locally. Use GitHub or GitLab; the lesson is platform-independent where possible.

Create this starting layout:

```text
capstone/
├── app/          # Application source code (added in later modules)
├── infra/        # Terraform and infrastructure definitions
├── deploy/       # Deployment manifests and GitOps configuration
├── README.md
└── .gitignore
```

Git does not track empty directories; add a small `.gitkeep` file inside `app/`, `infra/` and `deploy/` until they contain real source files.

Your `README.md` should explain what the capstone is, what each directory contains and how to contribute changes.

**Example `.gitignore`:**

```gitignore
# Secrets and local configuration
.env
.env.*
!.env.example
*.pem
*.key

# Build and local dependencies
node_modules/
dist/
build/

# Terraform local state and provider data
.terraform/
*.tfstate
*.tfstate.*
*.tfplan
crash.log
override.tf
override.tf.json
*_override.tf
*_override.tf.json
```

You may need additional ignore rules for your chosen technology. Commit a safe `.env.example` containing placeholder variable names, never real credentials. Terraform dependency lockfiles (such as `.terraform.lock.hcl`) are generally committed, not ignored.

**Verify the rules:**

```bash
git status --short
git check-ignore -v .env
git check-ignore -v infra/example.tfstate
```

The last two commands test patterns even if the example files do not exist. If a secret was *already committed*, adding it to `.gitignore` is insufficient: remove it from tracking and rotate exposed credentials as appropriate.

## 4. Branch, review and merge a change

Starting from `main`, create a small documentation change in a feature branch:

```bash
git switch main
git pull --ff-only
git switch -c feature/document-repository-layout
# Edit README.md
git status
git diff
git add README.md
git commit -m "docs: describe repository layout"
git push -u origin feature/document-repository-layout
```

Open a **pull request** (GitHub) or **merge request** (GitLab) targeting `main`. Include:

- What changed and why.
- How you checked it.
- Any open questions or risks.

Inspect the diff in the hosting platform and leave at least one meaningful review comment. If a second reviewer is available, request their review; otherwise document a self-review and note that it is **not equivalent to independent approval**.

Merge through the pull/merge request. Then:

```bash
git switch main
git pull --ff-only
git log --oneline --graph --decorate -n 8
```

Confirm your change appears in `main` and that the request records the merge.

## 5. Protect the default branch

In your hosting platform's repository settings, configure a branch protection rule or ruleset for `main` where your account permissions and plan allow it.

Aim to:

- Prevent accidental deletion or force-pushing to `main`.
- Require changes to arrive through pull/merge requests.
- Require at least one independent approval **when collaborators are available**.
- Enable checks before merging once a CI workflow exists (introduced in D03).

**Test it:** attempt a harmless direct push to `main` only after protection is configured, and record whether it is rejected. Do not overwrite history or try to bypass the rule. Some platforms and repository plans restrict enforcement features, especially for solo or private repositories: record what you could actually configure and what remains a limitation.

## Capstone lab — required deliverable

Create a **structured, branch-protected project repository** and merge one feature through a documented review workflow.

| Check | Evidence of completion |
| --- | --- |
| Remote access | SSH authentication test works; remote URL is configured |
| Repository layout | `app/`, `infra/`, `deploy/`, `README.md` and `.gitignore` present |
| Safe file handling | Ignore checks demonstrate exclusion of local credentials and Terraform state |
| Branch workflow | Feature branch contains a focused commit with an understandable message |
| Code review | Pull/merge request contains a description, review evidence and merge record |
| Branch protection | Rule/settings visible; enforcement demonstrated or limitations documented |
| History | The merged change is visible on `main` |

**Completion standard:** You can reproduce the feature-branch → review → merge workflow and explain each check. A functioning repository and its history are more important than a written assessment.

## Evidence to retain

Record the repository URL, pull/merge request URL, a short note about branch protection, and the commands or screenshots used to verify ignore rules and the final history. **Do not include authentication secrets, private keys or confidential repository content.**

## Further learning

- [Pro Git — Getting Started](https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control)
- [Pro Git — Git Branching](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell)
- [Git documentation — gitignore](https://git-scm.com/docs/gitignore)
- [GitHub — Connect with SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [GitHub — About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

**Next module:** [D02 — Docker & Containerization](D02_Docker_and_Containerization.md)
