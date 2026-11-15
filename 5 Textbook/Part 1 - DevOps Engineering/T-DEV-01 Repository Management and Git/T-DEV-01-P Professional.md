# T-DEV-01-P — Professional Engineering

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-p"></a>
#### T-DEV-01-P — Professional Engineering

## Why this level exists

Intermediate skill keeps *your* history coherent. Professional skill designs the repository so a *team* can change software safely: where each kind of change belongs, who must review it, what must pass before it enters the default branch, what must never be committed, and how a deployed artifact can be traced to reviewed source.

A repository that answers those questions consistently is a **developer interface**, not merely storage. Folder names alone do not create separation of duty; ownership rules plus enforced review do.

If Git mechanics are rusty, use [T-DEV-01-I](T-DEV-01-I%20Intermediate.md#t-dev-01-i) as a refresher. This section assumes you can branch, merge, revert and read a three-dot diff. Examples use a fictional organisation `example-org`, a service `orders-platform`, and GitHub-style syntax where a concrete syntax is needed; other hosts offer equivalents under different names. Configuration shown is *illustrative*: verify field names against your host’s current documentation before applying it.

## Repository architecture as a product decision

| Model | Strength | Cost | Typical fit |
| --- | --- | --- | --- |
| Monorepo | Atomic cross-component changes; shared visibility | Permission coupling; pipeline cost; noisy ownership | Strong platform tooling; high coordination needs |
| Multi-repo | Independent release and access policies | Cross-repo version coordination | Clear team boundaries; different cadences |
| Separate deployment-configuration repo | Clear approval boundary for production desired state | Extra promotion step; more repositories | Strict change control for runtime config |

Decide using change frequency, ownership, secret boundaries, tooling maturity and operational risk — not fashion. Record the decision.

A practical scoring pass makes the trade-off visible. Rate each pressure from 0 (irrelevant) to 3 (decisive) and write the reason beside the number:

| Pressure | Weight for this team | Favours | Reason |
| --- | --- | --- | --- |
| Changes routinely span app and infra | 3 | Monorepo | One PR can change both and be tested together |
| Platform team must approve every runtime change | 3 | Separate deploy repo, or path ownership | Approval boundary must be unambiguous |
| Different release cadence per component | 1 | Multi-repo | Not yet a pain |
| Contributors outside the organisation | 0 | — | Not applicable |
| CI minutes cost at current size | 1 | Multi-repo or path filters | Revisit if pipelines exceed 20 minutes |

The score is not the decision; it is the *evidence for* the decision, and it is what you revisit when circumstances change.

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

### ADR review drill

Give a colleague a draft ADR and require them to answer these questions in writing. An ADR that cannot answer them is not ready:

1. Which alternative was the *strongest* competitor, and what single fact made you reject it?
2. Which consequence of your decision will annoy someone in six months, and who?
3. What observable fact would make you reopen this decision? (A number, an event or a date — not “if needed”.)
4. Where is the evidence stored, and could a new engineer reproduce it?
5. What does this decision *not* protect against?

Below is a deliberately weak ADR. List every defect before reading the answer.

```markdown
# ADR 0002 — Use squash merges
Status: Accepted
Decision: We will squash merge everything because it is cleaner.
```

Defects: no context (who decided, for what team size); “cleaner” is a preference, not a criterion; no alternatives; no consequence statement (bisect granularity collapses, backports of partial work become harder); no evidence; no revisit trigger; no owner. A professional rewrite names the criterion (“reviewers read one commit per change”), states the cost (“bisect inside a squash is unavailable, so PRs are capped at 400 changed lines”) and the trigger (“reopen if mean PR size exceeds the cap or an incident takes longer than N hours to localise”).

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

| Role | Read | Propose (PR) | Approve | Merge to `main` | Edit workflows | Administer repo |
| --- | --- | --- | --- | --- | --- | --- |
| Contributor | Yes | Yes (fork or branch) | No | No | No | No |
| App maintainer | Yes | Yes | `/app/` only | After checks and approval | No | No |
| Platform maintainer | Yes | Yes | `/infra/`, `/deploy/`, `/.github/` | After checks and approval | Yes, via PR | No |
| Repository admin | Yes | Yes | By policy, not self-approval | Only through the same rules | Via PR | Yes — few people, logged |
| Automation identity | Yes | Yes (bot PRs) | Never | Never | Never | Never |

### Ownership rules that look right and are wrong

CODEOWNERS uses a **last-match-wins** rule: when several patterns match a path, the *last* matching line applies. This silently breaks coverage:

```text
/infra/                      @example-org/platform-team
*.tf                         @example-org/app-team
```

A change to `infra/network.tf` matches both; the later `*.tf` line wins, so the *app* team owns infrastructure code. Put broad patterns first and narrow ones last:

```text
*.tf                         @example-org/app-team
/infra/                      @example-org/platform-team
```

Other traps to test explicitly:

- A directory pattern without a leading slash (`infra/`) matches `infra/` at *any* depth, including `vendor/infra/`.
- A file path with a typo owns nothing, and no error is raised on many hosts.
- An owner team with **no write access** to the repository cannot satisfy the rule. Reviews are requested but never count.
- A code-owner rule that applies to the *author* gives self-approval unless the host forbids it. Check “require approval from someone other than the last pusher”.
- Owners on a protected path need a **deputy**. A team of one blocks every change while on leave, which breeds bypass.

Lint it in CI so rot is detected the day it happens:

```bash
# Illustrative: fail if CODEOWNERS references a path that does not exist
grep -vE '^\s*(#|$)' .github/CODEOWNERS | awk '{print $1}' | while read -r p; do
  path="${p#/}"
  case "$path" in *'*'*) continue ;; esac
  [ -e "$path" ] || { echo "CODEOWNERS path not found: $p"; exit 1; }
done
```

## Branch protection and rulesets

On the default branch, require at least:

- pull requests (no direct pushes)
- required approvals
- required status checks that actually gate quality
- code-owner review for owned paths
- block force-push and branch deletion
- linear history *only if* the team deliberately chose that trade-off

Protection rules are enforcement; CONTRIBUTING.md is intent. If the host plan cannot enforce a control, write “not enforceable here” and name a compensating control — do not pretend the screenshot of a desired setting is safety.

### A ruleset, written as data

Hosts that support rulesets can export them as structured data, which is better than screenshots because it can be reviewed, diffed and applied again. An illustrative shape (field names follow GitHub’s ruleset API; check your host):

```json
{
  "name": "protect-main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "bypass_actors": [
    { "actor_type": "Team", "actor_id": 0, "bypass_mode": "pull_request" }
  ],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "require_code_owner_review": true,
        "dismiss_stale_reviews_on_push": true,
        "require_last_push_approval": true,
        "required_review_thread_resolution": true
      } },
    { "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [ { "context": "ci/build" }, { "context": "ci/test" }, { "context": "security/secret-scan" } ]
      } }
  ]
}
```

Read it like a reviewer:

| Setting | What it buys | What it does not buy |
| --- | --- | --- |
| `non_fast_forward` | History cannot be rewritten on `main` | Protection of other branches that releases are cut from |
| `require_code_owner_review` | Owned paths need owner approval | That CODEOWNERS is correct |
| `dismiss_stale_reviews_on_push` | New commits invalidate old approvals | Review quality |
| `require_last_push_approval` | The pusher cannot approve their own final push | Collusion between two people |
| `strict_required_status_checks_policy` | Branch must be up to date with `main` before merge | That the checks test the right thing |
| `bypass_actors` with `pull_request` mode | Bypassers can only bypass via a PR, not by direct push | Absence of bypass — it still exists and must be audited |

### Required checks that cannot be satisfied (and ones that are always satisfied)

A required check is matched **by name**. Two classic failures:

- The check is renamed in the workflow (`build` → `build-and-test`), the rule still names `build`, and every PR is blocked forever — or, on some hosts, a skipped job counts as passing and the gate silently disappears.
- A check is path-filtered so it does not run for a docs-only PR; the required status never reports, and the merge is blocked. The usual remedy is a lightweight always-run job that reports the required name and conditionally runs the real work.

Test both by opening a harmless pull request that should be blocked and observing that it is.

### Evidence versus assertion

| Assertion | Weak “evidence” | Stronger evidence |
| --- | --- | --- |
| Default branch is protected | Screenshot of settings | Attempted direct push rejected |
| Code owners required | CODEOWNERS file exists | PR touching `/infra/` blocked without owner |
| Secrets blocked | Policy document | Push of a known test pattern rejected (use a fake non-live pattern your scanner recognises in a disposable repo) |

### Enforcement test lab

Run these in a disposable repository that carries the same ruleset as production. Record the exact rejection message; that message *is* the evidence.

```bash
# 1. Direct push to the protected branch must fail
git switch main && echo "x" >> README.md && git commit -am "test: direct push"
git push origin main
# Expect: remote rejected; message names the rule (pull request required)

# 2. Force-push must fail
git push --force origin main
# Expect: rejected (non-fast-forward / force-push blocked)

# 3. Branch deletion must fail
git push origin --delete main
# Expect: rejected (deletion blocked)

# 4. A PR touching /infra/ without owner approval must show "blocked"
git switch -c test/owner-gate && echo "# t" >> infra/README.md
git commit -am "test: touch infra" && git push -u origin test/owner-gate
# Expect: PR shows 'Review required from code owners'; merge button disabled

# 5. Fake secret pattern must be rejected by push protection (use your scanner's documented test string, never a real one)
```

Clean up afterwards by closing the pull request, deleting the test branch and resetting your local `main` with `git reset --hard origin/main`. Keep the log lines with date, repository and rule version in the repository’s evidence directory.

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

### Threat scenario catalogue

Work through each scenario using the same four columns: *what the attacker or accident does*, *which control should stop it*, *how you would observe that it did*, *what remains*.

| Scenario | Stopping control | Observable evidence | Residual risk |
| --- | --- | --- | --- |
| A contributor’s pull request edits a workflow so the publish step runs for pull-request events | Workflow-path ownership; no secrets for fork-triggered runs; least-privilege token defaults | Test PR from a fork cannot read the publishing secret | A maintainer approves a malicious workflow change |
| An owner’s account is phished and approves a hostile PR | Second reviewer on sensitive paths; phishing-resistant authentication; session and token review | Anomalous-login alert; review by two distinct identities | Compromise of two accounts |
| A dependency maintainer publishes a new hostile patch version | Lock files; pinned digests; review of lock-file diffs; delayed adoption window | Lock-file changes appear as a distinct reviewed diff | Zero-day in a pinned version |
| A developer commits a cloud key to a feature branch | Push protection; pre-commit scan; short-lived credentials | Push rejected, or alert within minutes | Key already copied before alert |
| An admin disables a rule “just for an hour” | Rule changes logged and alerted; rulesets managed as code | Audit-log event with actor and time | A bypass nobody reads |
| A release tag is moved to a different commit | Tag protection; artifacts built from digests, not tags | Tag-update event; digest mismatch in verification | Consumers resolving by tag name |
| Squash merge hides a malicious change inside a huge diff | PR size limits; required reviewers; scanning of the combined diff | Median PR size and review time tracked | Reviewer fatigue |

### Branch naming and commit policy

A small, consistent convention supports tooling and reading:

- Branch names `type/short-description`, for example `feat/retry-limit`, `fix/null-order`, `docs/adr-0003`, `chore/bump-lockfile`.
- Commit messages in imperative mood with a tracker reference; optionally a structured prefix (`feat:`, `fix:`, `docs:`) if you generate changelogs from them.
- A DCO sign-off or signed commits *only if* the organisation can operate the key lifecycle.

Enforce what can be enforced: a commit-message lint on pull requests, a PR-title check when squash merging (the PR title *becomes* the commit), and a ban on merge commits inside feature branches if you chose linear history.

## Secrets: prevention, detection, response

Controls form three layers, and each catches what the previous one missed:

| Layer | Control | Where it runs | Weakness |
| --- | --- | --- | --- |
| Prevention | `.gitignore`, secret manager, environment injection | Developer machine | Voluntary |
| Local detection | `pre-commit` hook running a scanner | Developer machine | Can be skipped with `--no-verify` |
| Server detection | Push protection and repository scanning | Host | Misses unknown formats |
| Response | Rotation runbook, revocation, audit | Organisation | Slow if untested |

An illustrative local hook configuration:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0        # pin an exact version you have reviewed
    hooks:
      - id: gitleaks
```

Because a local hook is skippable, the *server* check is the control; the local hook is a convenience that shortens the feedback loop. Never treat the two as equivalent.

## If a secret was committed

1. **Revoke or rotate the secret first.** Assume compromise.
2. Assess exposure: default branch? forks? CI logs? package registries?
3. Removing the file in a new commit does **not** remove it from history, clones or caches.
4. History rewriting (filter tools, force-push coordination) is a separate, disruptive incident response with a communication plan — never a substitute for rotation.

### Secret-leak runbook skeleton

| Step | Action | Evidence to keep |
| --- | --- | --- |
| 0 | Declare an incident; name an owner and a communication channel | Incident id and timestamp |
| 1 | Revoke or rotate the credential at its issuer | Issuer audit log showing revocation time |
| 2 | Check the credential’s activity since the commit time | Query results, including “no unexpected use” |
| 3 | Identify every location: commits, forks, pull-request refs, CI logs, artifacts, mirrors | Inventory table |
| 4 | Decide whether to rewrite history (policy decision, not reflex) | Decision record |
| 5 | If rewriting: announce a freeze, rewrite, force-push with a coordinated window, ask all contributors to re-clone | Announcement and completion confirmation |
| 6 | Add or fix the control that failed | Merged PR; test that the pattern is now blocked |
| 7 | Blameless review within a set number of days | Review document |

### Drill: first hour after a leak

A live API token is found in a commit on a feature branch that has been pushed for two days and mirrored into CI logs. Write your answers to:

1. Which action happens first, and why is it *not* “delete the file”?
2. Who must be told within the first hour, and what do you ask them to do?
3. Which evidence would show whether the token was *used* by someone else?
4. What is the decision criterion for or against rewriting history in this case?
5. Which control failed, and what test proves it now works?

A strong answer to (4) weighs the credential’s value after rotation (if it is dead, the leak has little value and a rewrite may cost more than it saves) against any non-credential sensitive data in the same commit (which a rotation cannot recall).

## History policy for a platform-minded team

History is an operational asset. It must support:

- **Traceability** — artifact → reviewed commit
- **Auditability** — who approved what
- **Reproducibility** — CI must not follow a moving mutable tag for an immutable release
- **Coordination** — humans can read what landed
- **Developer experience** — reviewable diffs

A common defensible policy: all changes via pull request; squash small branches; merge-commit complex long-lived feature work when topology matters; tag releases; forbid force-push to the default branch. Document maintainers, review rules, tagging, backport method and how builds embed commit identifiers into artifacts.

### Release and backport policy

| Decision | Option A | Option B | Choose A when | Choose B when |
| --- | --- | --- | --- | --- |
| Release source | Tag on `main` | Dedicated `release/x.y` branch | You ship continuously from one line | You support several versions concurrently |
| Fix on old versions | Cherry-pick `-x` from `main` | Fix on release branch, forward-port | Fix originates on `main` | Fix is version-specific |
| Version identity | Annotated tag | Tag plus build metadata | Source alone identifies release | Build provenance must be attached |

Write down: who may create release tags, whether tags are protected from update or deletion, how backports are labelled, and how a release is *withdrawn*. A tag that can be moved is not an identifier.

## Onboarding as a testable artifact

Maintain `CONTRIBUTING.md` that tells a stranger:

- how to obtain tools and authenticate to the host
- where changes of each kind belong
- branch naming and commit message expectations
- what validation to run before review
- who reviews which paths
- how to report an exposed credential

**Professional exercise:** follow CONTRIBUTING.md from a fresh clone on a clean machine account and file every missing step as a defect in the document.

A skeleton you can adapt:

```markdown
# Contributing

## Setup
1. Install Git >= 2.40 and the tools listed in docs/tooling.md.
2. Clone, then run `make bootstrap` (installs hooks, verifies tool versions).
3. Authenticate to the host with SSH or a fine-grained token; never reuse a personal-admin token.

## Making a change
1. `git switch -c feat/<short-name>` from an up-to-date `main`.
2. Keep the change to one purpose; split refactors from behaviour changes.
3. Run `make check` before pushing; paste the summary in the PR.
4. Open a PR using the template; link the tracker item.

## Who reviews what
See `.github/CODEOWNERS`. Changes to `/.github/` and `/infra/` need platform review.

## If you committed a secret
Do not delete and hope. Revoke it, then follow `docs/runbooks/secret-leak.md` and tell #security immediately.
```

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
| Change who owns a path | PR to CODEOWNERS with owner approval | Editing host settings quietly |
| Add a required check | Add it as a ruleset change with a test PR | Renaming a job without updating the rule |

## Knowledge consolidation

- Repository layout is a **product** decision with revisit criteria.
- Ownership without enforcement is theatre; permission without ownership is unmanaged risk.
- Supply-chain controls have **stated limits**; write those limits down.
- Rotate secrets before rewriting history.
- Prefer observable rejection as evidence of enforcement.
- CODEOWNERS is last-match-wins; test the *matching*, not just the file.
- Required checks are matched by name: renames and path filters can disable a gate silently.
- A local hook is convenience; the host-side check is the control.

## Exercises

**Exercise 1.** For a fictional two-team service, write ADR 0001 choosing mono- vs multi-repo vs separate deploy-config repo. Include alternatives, consequences, evidence and a revisit trigger.

**Exercise 2.** Draft CODEOWNERS and a permission matrix. List three harmless enforcement tests and the observable result each should produce. Mark any control your current host plan cannot enforce and name a compensating control.

**Exercise 3 (challenge).** Describe the first three actions after discovering a live API token in a pushed commit on `main`, in order, and explain why deleting the file in a follow-up commit is insufficient.

**Exercise 4 — Ruleset review.** Given the ruleset JSON above, list five ways a determined insider could still land an unreviewed change (for example via a bypass actor, an unprotected release branch, a workflow change, an admin editing the rule, or two colluding reviewers) and the detective control that would reveal each.

**Exercise 5 — Ownership lint.** Write a CI script that fails when a CODEOWNERS pattern matches no files, when a team named in the file is not in a list you maintain, or when `/.github/` has no owner. State what class of rot each check catches.

**Exercise 6 — Threat table.** Add three scenarios of your own to the threat catalogue using the four columns, including one that involves a third-party action or dependency and one that involves a mirror or backup host.

**Exercise 7 — ADR rewrite.** Rewrite ADR 0002 (“Use squash merges”) so that it passes the five review questions.

**Solution notes.** Exercise 3 must begin with revocation/rotation, not history deletion. Enforcement tests should cite rejected pushes or blocked merges, not screenshots alone.

**Solution notes (Exercise 4).** Typical answers: admin bypass (alert on bypass events); release branches without rules (apply a ruleset pattern `release/*`); a workflow edit that changes what checks run (workflow-path ownership); an admin weakening the rule (audit-log alert, ruleset-as-code with drift detection); reviewer collusion (require two reviewers on sensitive paths and sample reviews).

**Solution notes (Exercise 5).** The unused-pattern check catches renamed directories; the team-list check catches leavers and renames; the `/.github/` check catches the privileged-workflow gap. None proves the *people* are competent reviewers.

**Solution notes (Exercise 7).** A passing rewrite states the criterion, the cost (loss of intra-PR bisect), a mitigation (PR size cap), evidence (mean PR size, incident-localisation time) and a trigger to revisit.
