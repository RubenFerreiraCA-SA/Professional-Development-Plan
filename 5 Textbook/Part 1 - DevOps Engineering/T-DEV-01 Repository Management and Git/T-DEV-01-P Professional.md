# T-DEV-01-P — Professional Engineering

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-p"></a>
#### T-DEV-01-P — Professional Engineering

## Why this level exists

Intermediate skill keeps *your* history coherent. Professional skill designs the repository so a *team* can change software safely: where each kind of change belongs, who must review it, what must pass before it enters the default branch, what must never be committed, and how a deployed artifact can be traced to reviewed source.

A repository that answers those questions consistently is a **developer interface**, not merely storage. Folder names alone do not create separation of duty; ownership rules plus enforced review do.

If Git mechanics are rusty, use [T-DEV-01-I](T-DEV-01-I%20Intermediate.md#t-dev-01-i) as a refresher. This section assumes you can branch, merge, revert and read a three-dot diff.

## Repository architecture as a product decision

| Model | Strength | Cost | Typical fit |
| --- | --- | --- | --- |
| Monorepo | Atomic cross-component changes; shared visibility | Permission coupling; pipeline cost; noisy ownership | Strong platform tooling; high coordination needs |
| Multi-repo | Independent release and access policies | Cross-repo version coordination | Clear team boundaries; different cadences |
| Separate deployment-configuration repo | Clear approval boundary for production desired state | Extra promotion step; more repositories | Strict change control for runtime config |

Decide using change frequency, ownership, secret boundaries, tooling maturity and operational risk — not fashion. Record the decision.

### Worked ADR pattern

```markdown
# ADR 0001 — Repository strategy
Status: Accepted
Context: Two teams (application, platform). Infra changes need platform review.
Decision: Single repository; infra/ and deploy/ owned by platform; main protected.
Alternatives considered:
  - Separate infra repo — rejected for now (coordination cost at this team size).
Consequences: Coupled pipelines; shared clone size.
Evidence: Branch-rule export; CODEOWNERS; test PR links.
Revisit when: Release cadences diverge or team count exceeds N.
```

An ADR that only states preference without alternatives and revisit triggers is incomplete.

## Ownership is not permission

*Ownership* names who is accountable for reviewing a scope. *Permission* is what the platform allows an identity to do. Express ownership in a code-owners file and **enforce** it with branch rules:

```text
# CODEOWNERS (GitHub syntax; paths are repository-root relative)
/app/            @example-org/app-team
/infra/          @example-org/platform-team
/deploy/         @example-org/platform-team
/.github/        @example-org/platform-team
/docs/decisions/ @example-org/app-team @example-org/platform-team
```

Common failure modes:

| Failure | Why it happens | Detection |
| --- | --- | --- |
| Owners lack write access | Rule cannot be satisfied | Test PR never becomes mergeable |
| “Requested” but not “required” review | Advice, not control | Merge without owner approval succeeds |
| Administrator bypass | Emergency path used casually | Audit log of bypass events empty or ignored |
| Stale teams in CODEOWNERS | Renames and leavers | CI lint of owners file fails |

Build a **permission matrix** of roles against actions (read, propose, approve, merge, change workflows, administer) and write the reason for every restriction.

## Branch protection and rulesets

On the default branch, require at least:

- pull requests (no direct pushes)
- required approvals
- required status checks that actually gate quality
- code-owner review for owned paths
- block force-push and branch deletion
- linear history *only if* the team deliberately chose that trade-off

Protection rules are enforcement; CONTRIBUTING.md is intent. If the host plan cannot enforce a control, write “not enforceable here” and name a compensating control — do not pretend the screenshot of a desired setting is safety.

### Evidence versus assertion

| Assertion | Weak “evidence” | Stronger evidence |
| --- | --- | --- |
| Default branch is protected | Screenshot of settings | Attempted direct push rejected |
| Code owners required | CODEOWNERS file exists | PR touching `/infra/` blocked without owner |
| Secrets blocked | Policy document | Push of a known test pattern rejected (use a fake non-live pattern your scanner recognises in a disposable repo) |

## The repository as a supply-chain boundary

Trust must follow a change from author toward production. Design controls by purpose and state honestly what each does **not** prove.

| Control | Reduces | Does not prove |
| --- | --- | --- |
| Protected default branch | Unreviewed or destructive history edits | That merged changes are secure |
| Code-owner review | Skipping domain review | That reviewers are infallible |
| Secret scanning / push protection | Known credential patterns entering source | That every secret form is found |
| Scoped, short-lived tokens | Blast radius of token theft | That allowed actions cannot be abused |
| Signed commits/tags | Some identity spoofing | That signed content is benign |
| Required CI checks | Merging without declared validations | That tests cover all risks |

### Worked threat: privileged workflow files

An external contributor opens a pull request that edits a workflow file under `.github/workflows/`. The application diff looks harmless. The workflow runs with a publishing token.

Ask, for every repository automation event:

1. What triggers the automation?
2. What permissions does untrusted code receive?
3. Which refs are allowed to publish artifacts?
4. Who can change workflow files, and who must approve that change?
5. How would a suspicious change be detected, revoked and investigated?

Treat workflow paths as security-sensitive ownership, not “just CI config”.

## If a secret was committed

1. **Revoke or rotate the secret first.** Assume compromise.
2. Assess exposure: default branch? forks? CI logs? package registries?
3. Removing the file in a new commit does **not** remove it from history, clones or caches.
4. History rewriting (filter tools, force-push coordination) is a separate, disruptive incident response with a communication plan — never a substitute for rotation.

## History policy for a platform-minded team

History is an operational asset. It must support:

- **Traceability** — artifact → reviewed commit
- **Auditability** — who approved what
- **Reproducibility** — CI must not follow a moving mutable tag for an immutable release
- **Coordination** — humans can read what landed
- **Developer experience** — reviewable diffs

A common defensible policy: all changes via pull request; squash small branches; merge-commit complex long-lived feature work when topology matters; tag releases; forbid force-push to the default branch. Document maintainers, review rules, tagging, backport method and how builds embed commit identifiers into artifacts.

## Onboarding as a testable artifact

Maintain `CONTRIBUTING.md` that tells a stranger:

- how to obtain tools and authenticate to the host
- where changes of each kind belong
- branch naming and commit message expectations
- what validation to run before review
- who reviews which paths
- how to report an exposed credential

**Professional exercise:** follow CONTRIBUTING.md from a fresh clone on a clean machine account and file every missing step as a defect in the document.

## Decision guide (quick reference)

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| See how branches diverged | `git log --graph --decorate --oneline --all`, `git merge-base` | Guessing from branch names |
| Review a feature | `git diff main...feature` | Confusing two- and three-dot diffs |
| Inspect what will be committed | `git diff --cached` | Trusting only the editor tab |
| Undo a published change | Reviewed `git revert` | Reset + force-push on shared refs |
| Recover unpublished work | `git reflog`, then a recovery branch | Reflexive hard resets |
| Find a regression | Deterministic test + `git bisect` | Blaming the chronologically latest commit |
| Prove a control | Harmless failing attempt | Screenshots of settings alone |

## Knowledge consolidation

- Repository layout is a **product** decision with revisit criteria.
- Ownership without enforcement is theatre; permission without ownership is unmanaged risk.
- Supply-chain controls have **stated limits**; write those limits down.
- Rotate secrets before rewriting history.
- Prefer observable rejection as evidence of enforcement.

## Exercises

**Exercise 1.** For a fictional two-team service, write ADR 0001 choosing mono- vs multi-repo vs separate deploy-config repo. Include alternatives, consequences, evidence and a revisit trigger.

**Exercise 2.** Draft CODEOWNERS and a permission matrix. List three harmless enforcement tests and the observable result each should produce. Mark any control your current host plan cannot enforce and name a compensating control.

**Exercise 3 (challenge).** Describe the first three actions after discovering a live API token in a pushed commit on `main`, in order, and explain why deleting the file in a follow-up commit is insufficient.

**Solution notes.** Exercise 3 must begin with revocation/rotation, not history deletion. Enforcement tests should cite rejected pushes or blocked merges, not screenshots alone.
