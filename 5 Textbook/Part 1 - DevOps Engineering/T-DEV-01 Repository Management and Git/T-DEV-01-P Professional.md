# T-DEV-01-P — Professional Engineering

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-p"></a>
#### T-DEV-01-P — Professional Engineering

**Repository architecture as a developer interface.** A newcomer should be able to answer without asking anyone: where does each kind of change belong, who reviews it, what must pass before it enters the default branch, what must never be committed, and how can a deployed artifact be traced to reviewed source. A repository that answers consistently is a product for its developers.

| Model | Strength | Cost |
| --- | --- | --- |
| Monorepo | Atomic cross-component changes, shared visibility | Permission coupling, pipeline cost, noisy ownership |
| Multi-repo | Independent release and access policies | Cross-repo version coordination |
| Separate deployment-configuration repo | Clear approval boundary for production desired state | A promotion step and more repositories |

There is no universally correct model. Decide on change frequency, ownership, secrets boundaries, tooling and operational risk — not fashion. A directory called `infra/` does not restrict who can edit it; separation of duty comes from ownership rules plus enforced review, not from folder names.

**Ownership is not permission.** *Ownership* names who is accountable for reviewing a scope. *Permission* is what the platform allows an identity to do. Express ownership in a code-owners file and enforce it with branch rules:

```text
# CODEOWNERS (GitHub syntax)
/app/            @example-org/app-team
/infra/          @example-org/platform-team
/deploy/         @example-org/platform-team
/.github/        @example-org/platform-team
/docs/decisions/ @example-org/app-team @example-org/platform-team
```

Pitfalls: the owning team must have write access or the rule cannot be satisfied; a rule that is "requested" but not "required" is advice, not control; administrators and bypass identities may be silently exempt.

Build a permission matrix of roles against actions (read, propose, approve, merge, change workflows, administer) and write down the reason for every restriction.

**Branch protection.** On the default branch require pull requests, required approvals, required status checks, code-owner review for owned paths, linear history if the team chose it, and block force-pushes and deletions. Protection rules are the enforcement; documentation is the intent.

**The repository as a supply-chain boundary.** Trust must follow the change from author to production. Design controls by purpose and state honestly what each does *not* prove.

| Control | Reduces | Does not prove |
| --- | --- | --- |
| Protected default branch | Unreviewed or destructive changes | That merged changes are secure |
| Code-owner review | Skipping domain review | That reviewers are infallible |
| Secret scanning (push protection) | Recognised credential patterns entering source | That every secret is found |
| Scoped, short-lived tokens | Blast radius of token theft | That allowed actions cannot be abused |
| Signed commits and tags | Some identity spoofing | That signed content is benign |
| Required CI checks | Merging without validations | That tests cover all risks |

A worked threat: an external contributor edits a workflow file that runs with a publishing token. The application code looks harmless, yet the workflow may leak credentials. Ask for every repository event: what triggers automation, what permissions untrusted code receives, which refs can publish, who can change workflow files and approve that change, and how a suspicious change would be detected, revoked and investigated.

**If a secret was committed.** Revoke or rotate it first. Deleting the file in a new commit does not remove it from history, clones or caches. History rewriting is a separate, coordinated, disruptive response, and it never replaces rotation.

**Decisions and onboarding as artifacts.** Record significant choices in short architecture decision records (ADRs):

```markdown
# ADR 0001 — Repository strategy
Status: Accepted
Context: Two teams, shared release cadence, infra changes need platform review.
Decision: Single repository; infra/ and deploy/ owned by platform; main protected.
Alternatives: Separate infra repo (rejected: coordination cost at this scale).
Consequences: Coupled pipelines; revisit if team count exceeds N.
Evidence: Branch-rule export, test PR link.
Revisit when: Release cadences diverge.
```

Maintain a `CONTRIBUTING.md` that tells a stranger how to obtain tools, where changes belong, how to name branches, what validation to supply, who reviews what and how to report an exposed credential. Test it by following it from a fresh clone and recording each missing instruction.

**History policy for a platform team.** History is an operational asset: it must support traceability (artifact to reviewed change), auditability, reproducibility (CI must not follow a moving ref in an immutable release), coordination and developer experience. A common policy: all changes via pull request, squash small branches, merge-commit complex feature work, tag releases, forbid force-push to the default branch. A fully linear policy is simpler to traverse but needs careful handling of shared branches. Document assumptions: maintainers, review rules, tagging, backports and how the build links artifacts to commits.

**Evidence versus assertion.** A screenshot of a rule shows a setting. A rejected unauthorised push shows enforcement. Test failure modes with harmless changes: a direct push to the protected branch, ignored secret files before they are staged, an `infra/` change without the owning reviewer, and whether an administrator is silently exempt. If a plan tier cannot enforce a control, say "not enforceable here" and describe the compensating control.

**Decision guide**

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| See how branches diverged | `git log --graph --decorate --oneline --all`, `git merge-base` | Guessing from names |
| Review a feature | `git diff main...feature` | Confusing two- and three-dot diffs |
| Inspect what will be committed | `git diff --cached` | Trusting the editor view |
| Undo a published change | A reviewed `git revert` | Reset plus force-push on shared refs |
| Recover unpublished work | `git reflog`, then a recovery branch | Hard resets as reflexive cleanup |
| Find a regression | A deterministic test plus `git bisect` | Blaming the latest commit |
