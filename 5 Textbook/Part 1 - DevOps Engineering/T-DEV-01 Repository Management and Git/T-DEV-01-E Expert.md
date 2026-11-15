# T-DEV-01-E — Expert Depth

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-e"></a>
#### T-DEV-01-E — Expert Depth

## Why this level exists

Professional practice designs enforceable repository controls for a team. Expert practice designs those controls for *organisations*: many teams, many repositories, emergency bypasses, long-lived release lines, supply-chain adversaries and migrations that cannot be undone casually. The skill is not knowing obscure flags; it is anticipating how accepted practices fail under scale, incentives and partial compromise.

Entrants who need mechanics should use [T-DEV-01-I](T-DEV-01-I%20Intermediate.md#t-dev-01-i) and [T-DEV-01-P](T-DEV-01-P%20Professional.md#t-dev-01-p). This section assumes protected branches, CODEOWNERS and revert-vs-reset are already clear.

## Integration strategies at organisational scale

| Strategy | Benefit at scale | Cost at scale | Expert failure mode |
| --- | --- | --- | --- |
| Squash to default branch | Cheap, readable mainline | Bisect granularity collapses to the squash | “Which micro-commit broke prod?” becomes unanswerable inside the squash |
| Merge commits | Feature topology preserved; revert whole feature often one operation | Noisier history; need fluency with `-m` when reverting merges | Re-merging a reverted feature without reverting the revert |
| Rebase-centric workflows | Clean review series | Shared-branch rewrite incidents | Force-push races; lost review context |
| Cherry-pick backports | Surgical fixes on release lines | Duplicate commit ids for one logical change | Silent double-apply or conflict storms on later merges |

Track backports explicitly: labels, release branches, or trailers from `git cherry-pick -x` (`(cherry picked from commit …)`). Without tracking, “is this fix on the release line?” becomes archaeology.

### Reverting a merge commit

```bash
# Mainline parent is usually parent 1; confirm with:
git show --format=raw <merge_sha> | head
git revert -m 1 <merge_sha>
```

If you later need the feature again, you typically revert the revert (or recreate the changes); simply merging the old branch often no-ops because Git considers those changes already present in history.

## Advanced tools and the risks they introduce

| Technique | Problem solved | Risk introduced | Mitigations |
| --- | --- | --- | --- |
| `git worktree` | Multiple branches checked out at once | Forgotten worktrees pin branches and disk | Periodic `git worktree list`; remove finished trees |
| `git rerere` | Reuse recorded conflict resolutions | A wrong resolution recurs silently | Review rerere cache; do not treat it as correctness |
| `git range-diff` | Compare patch series before/after rebase | Needs stable bases | Capture old tip before rebase |
| Sparse checkout / partial clone | Huge monorepos become usable | Tooling assuming full trees/history breaks | Document required clone flags for contributors |
| Submodules | Pin external dependency commits | Detached surprises; pinning drift | Prefer explicit versioning strategy; CI checks |
| Signed commits/tags | Stronger authorship claims | Key management burden; false content safety | Sign *and* still review; protect signing keys |

```bash
git worktree add ../orders-hotfix release/1.4
git range-diff origin/main...old-tip origin/main...new-tip
```

## Governance failure modes (case catalogue)

### 1. The bypass actor

Emergency merge without review can be necessary. Without logging, rarity targets and after-the-fact review, bypass becomes the normal path under deadline pressure. Expert design: inventory who holds bypass, alert on use, require a short incident note tying bypass to a tracked emergency.

### 2. Workflow files as privileged code

Anything that changes automation inherits the automation’s privileges. Owners of workflow paths are de facto security owners. Threat: a “docs” pull request that also tweaks a deploy workflow. Control: path-restricted CODEOWNERS, required reviews from a security/platform group, and restricted tokens that cannot publish from pull-request contexts of forks.

### 3. Review theatre

Mandatory approvals without enforceable checks and without attention to diff size produce rubber stamps. Measure review latency and change size; treat enormous diffs as process failures, not heroics.

### 4. Ownership rot

Teams rename; people leave; CODEOWNERS entries become unsatisfiable or silently wrong. Lint owners against live team membership in CI. Broken ownership is an availability and security incident waiting for a busy Friday.

### 5. History rewriting under pressure

Removing a leaked secret from *all* history requires coordinating every clone, fork, mirror, CI cache and package that may have fetched it. Treat rewriting as incident response with communications, not as a quiet `filter-repo` on Friday afternoon. Rotation remains mandatory even if rewrite succeeds.

## Designing standards across many repositories

Platform organisations standardise what must be common:

- default branch protection / rulesets
- required checks
- secret scanning
- CODEOWNERS linting
- repository templates for README/CONTRIBUTING/SECURITY
- restricted who can create public repositories

Apply the standard **as code** (host APIs, Terraform providers, internal provisioners) and detect drift. Hand-clicking settings across hundreds of repositories guarantees entropy.

Expert trade-off: central standards versus team autonomy. Too little standard → unreviewable variance. Too much → shadow IT repositories. Publish an exception process with expiry dates; eternal exceptions are ungoverned forks of policy.

## Traceability end to end

From a running artifact, an expert design can answer:

1. Which commit built it?
2. Who reviewed that commit?
3. Which workflow run produced the artifact?
4. Which approvals gated promotion?

That requires builds to embed commit and run identifiers into artifact metadata, protected refs so those commits remain reachable, and retention of review/run records for as long as the artifact may run. The weak link is rarely Git’s data model; it is human exception handling (“hotfix directly in prod console”) that bypasses the chain.

## Large-repository and migration trade-offs

| Pressure | Options | Consequences |
| --- | --- | --- |
| Monorepo clone/CI cost | Sparse checkout, partial clone, remote build caching, split pipelines by path | Contributor tooling complexity |
| Multi-repo version hell | Release trains, automated bump PRs, contract tests | Orchestration burden |
| Split a monorepo | `git filter-repo` into new remotes; freeze old paths | History continuity vs clean breaks; update every consumer |
| Merge many repos | Import with `git subtree` or rewrite; unify ownership | Short-term conflict; long-term ownership redesign |

Migrations fail socially more often than technically: if CODEOWNERS, CI paths and team habits still assume the old layout, the Git rewrite was the easy part.

## Adversarial and contested questions

Use these as design reviews, not trivia:

- Why can `git reset --hard` followed by force-push be legitimate on a private branch and a policy violation on the default branch in the same hour?
- What evidence would convince you CODEOWNERS is enforced for administrators, not only for ordinary contributors?
- Which of your controls still hold if a maintainer’s account is phished?
- If squash merges are mandatory, how do you bisect production regressions that landed inside a 2,000-line squash?
- When is a submodule preferable to vendoring or a monorepo package — and what operational pain are you accepting?

## Knowledge consolidation

- Scale turns local Git craft into **organisational control design**.
- Every powerful tool (`rerere`, rewrite, bypass, signatures) has a failure mode; name it in the design.
- Traceability is a chain; exceptions break the chain even when Git is healthy.
- Standards-as-code plus expiring exceptions beat wiki aspiration.
- Expert judgement is knowing when **not** to rewrite, rebase or centralise.

## Exercises

**Exercise 1.** Draft a one-page “repository standard” for 80 application repositories: mandatory controls, allowed team choices, exception process with expiry, and how drift is detected.

**Exercise 2.** Given a merge commit that brought a bad feature onto `main`, write the exact revert command sequence, then explain how you would re-introduce a fixed version of the feature without resurrecting the bug via a naive merge.

**Exercise 3 (challenge).** A secret was pushed to `main`, mirrored to a backup host, and built into a container registry layer. Outline the incident response across credential rotation, registry, mirrors and communication — and state which steps Git history rewrite cannot accomplish alone.

**Solution notes.** Exercise 2 should use `git revert -m 1` after confirming parents; re-introduction usually needs revert-of-revert or reimplemented commits. Exercise 3 must treat registry and mirrors as first-class exposure surfaces; rewrite without rotation is theatre.
