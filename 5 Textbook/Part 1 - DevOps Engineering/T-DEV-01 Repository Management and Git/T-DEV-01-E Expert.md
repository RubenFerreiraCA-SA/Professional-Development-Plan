# T-DEV-01-E — Expert Depth

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-e"></a>
#### T-DEV-01-E — Expert Depth

**Trade-offs of integration strategies at scale.** Squash merges make bisecting coarse but cheap; merge commits preserve context and make reverting a whole feature one operation (reverting a merge needs `-m 1` to pick the mainline parent, and re-merging the branch later requires reverting the revert); rebase workflows need discipline around shared branches and tooling such as `git range-diff` to review a rewritten series. Cherry-picked backports duplicate a logical change under a different commit id, and later merges of the two lines can conflict or silently double-apply. Mature teams track backports explicitly (labels, release branches, or "(cherry picked from commit …)" trailers produced by `git cherry-pick -x`).

**Advanced techniques and their operational risks**

| Technique | Problem solved | Risk introduced |
| --- | --- | --- |
| `git worktree` | Several branches checked out at once | Forgotten worktrees pin branches and disk |
| `git rerere` | Reuse recorded conflict resolutions | A wrong recorded resolution recurs silently |
| `git range-diff` | Compare patch series before and after rebase | Needs stable base references |
| Sparse checkout and partial clone | Huge repositories | Tooling that assumes full history may break |
| Submodules vs monorepo | Cross-repo dependency | Pinning drift, surprise detached states |
| Signed commits and tags | Provenance of authorship | Key management burden; false sense of content safety |

**Governance failure modes.**

1. *The bypass actor.* Emergency access that skips review is necessary, but must be rare, logged and reviewed afterwards. Audit who holds it.
2. *Workflow files as privileged code.* Anything that changes automation runs with the automation's privileges; owners of workflow paths are effectively security owners.
3. *Review theatre.* Mandatory approvals without enforced checks produce rubber-stamping. Measure review latency and size; large diffs are rarely reviewed meaningfully.
4. *Ownership rot.* Teams are renamed and people leave; stale code-owner entries turn into unsatisfiable rules or unowned paths. Lint the owners file in CI.
5. *History rewriting under pressure.* Removing a leaked secret from all history requires coordination with every clone, fork, mirror and cache. Treat rewriting as incident response with a communication plan, not as a fix.

**Designing for large and many repositories.** Platform teams standardise what is common across repositories (branch rules, required checks, secret scanning, templates, owners-file linting) and leave application choices to teams. Apply the standard as code — through the hosting provider's API or Terraform provider — and detect drift from it, rather than configuring each repository by hand.

**Traceability end to end.** An expert design can answer, from a running artifact, which commit built it, who reviewed it, which workflow run produced it and which approvals gated it. That requires the build to record the commit and run identifiers in artifact metadata, protected refs so the commit is stable, and retention of review and run records for as long as the artifact may run. The weak link is usually not Git but the human process around exceptions.

**Mentoring prompts.** Why can `git reset --hard` followed by a force-push be both a legitimate private-branch operation and a policy violation on the default branch? What evidence would convince you that a code-owner rule is enforced for administrators? Which of your controls would still hold if a maintainer's account were compromised?

---
