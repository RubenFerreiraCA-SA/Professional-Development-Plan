# T-DEV-01-E — Expert Depth

*Chapter: [T-DEV-01 — Repository Management and Git](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-01-e"></a>
#### T-DEV-01-E — Expert Depth

## Why this level exists

Professional practice designs enforceable repository controls for a team. Expert practice designs those controls for *organisations*: many teams, many repositories, emergency bypasses, long-lived release lines, supply-chain adversaries and migrations that cannot be undone casually. The skill is not knowing obscure flags; it is anticipating how accepted practices fail under scale, incentives and partial compromise.

Entrants who need mechanics should use [T-DEV-01-I](T-DEV-01-I%20Intermediate.md#t-dev-01-i) and [T-DEV-01-P](T-DEV-01-P%20Professional.md#t-dev-01-p). This section assumes protected branches, CODEOWNERS and revert-vs-reset are already clear. Examples use a fictional organisation `example-org` with roughly eighty application repositories. Configuration and outputs are *illustrative*: verify syntax against current documentation for your Git version and host, and rehearse destructive operations on a disposable clone.

## Integration strategies at organisational scale

| Strategy | Benefit at scale | Cost at scale | Expert failure mode |
| --- | --- | --- | --- |
| Squash to default branch | Cheap, readable mainline | Bisect granularity collapses to the squash | “Which micro-commit broke prod?” becomes unanswerable inside the squash |
| Merge commits | Feature topology preserved; revert whole feature often one operation | Noisier history; need fluency with `-m` when reverting merges | Re-merging a reverted feature without reverting the revert |
| Rebase-centric workflows | Clean review series | Shared-branch rewrite incidents | Force-push races; lost review context |
| Cherry-pick backports | Surgical fixes on release lines | Duplicate commit ids for one logical change | Silent double-apply or conflict storms on later merges |

Track backports explicitly: labels, release branches, or trailers from `git cherry-pick -x` (`(cherry picked from commit …)`). Without tracking, “is this fix on the release line?” becomes archaeology.

`git cherry` compares by *patch identity* rather than commit id, so it recognises a backport even though the id differs:

```bash
git fetch origin
git cherry -v origin/release/1.4 origin/main
```

Illustrative output:

```text
+ 5be0f12a9c3d fix: cap payment retries
- 7c41d9e03b52 fix: null order id on empty cart
+ a1d03f77e8c4 feat: add order export
```

A leading `-` means an equivalent patch is already on `release/1.4`; `+` means it is not. A release manager can turn that into a checklist of what was deliberately left out versus forgotten.

### Reverting a merge commit

```bash
# Mainline parent is usually parent 1; confirm with:
git show --format=raw <merge_sha> | head
git revert -m 1 <merge_sha>
```

If you later need the feature again, you typically revert the revert (or recreate the changes); simply merging the old branch often no-ops because Git considers those changes already present in history.

### Lab: revert a merge, then bring the fixed feature back

```bash
mkdir revert-lab && cd revert-lab && git init -b main
printf 'v1\n' > app.txt && git add . && git commit -m "base"
git switch -c feature/export
printf 'export=buggy\n' > export.txt && git add . && git commit -m "feat: export (contains bug)"
git switch main && printf 'unrelated\n' > other.txt && git add . && git commit -m "unrelated work"
git merge --no-ff feature/export -m "Merge feature/export"
MERGE=$(git rev-parse HEAD)
```

Revert the merge and observe:

```bash
git revert -m 1 "$MERGE" --no-edit
ls                               # export.txt is gone; other.txt remains
git log --oneline --graph --all
```

Now add the fix on the feature branch and try the naive merge:

```bash
git switch feature/export
printf 'validated\n' > export-validation.txt && git add . && git commit -m "fix: validate export input"
git switch main
git merge feature/export
ls
```

Result: Git considers the original feature commit *already merged*, so only the new fix arrives. `export-validation.txt` is present but `export.txt` — the body of the feature — is **missing**, and nothing warns you. The repair is to revert the revert first:

```bash
git reset --hard HEAD~1                                   # abandon the incomplete merge (local lab only)
REV=$(git log --format=%H --grep='^Revert' -1)            # the commit that reverted the merge
git revert "$REV" --no-edit                               # restores the feature's changes
git merge feature/export -m "Merge fix"                   # brings the fix on top
ls
```

**Check:** `ls` should now list `app.txt`, `export.txt`, `export-validation.txt` and `other.txt`, and `git log --oneline` should show, in order, base, the feature commit, the merge, the revert, the fix, the revert-of-revert and the final merge. The lesson is not the commands but the ledger: Git remembers that a change was merged, independent of whether the change is currently *present*.

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
git range-diff origin/main old-tip new-tip
```

### Using rerere without trusting it

```bash
git config --global rerere.enabled true
git rerere status          # paths with recorded pre-images
git rerere diff            # the current recorded resolution
git rerere forget path/to/file   # drop a wrong recorded resolution
```

Rerere helps most when a long-lived integration branch is rebased repeatedly. The risk is invisible: a resolution that was wrong the first time is applied again without a conflict marker to warn you. After a rerere-assisted replay, run `git range-diff` against the previous tip and read the resolved hunks.

### Signing, verifying and what it proves

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
git log --show-signature -1
git log --format='%h %G? %GS %s' main~10..main
```

The `%G?` column shows `G` (good), `N` (no signature), `B` (bad), `E` (cannot check) and others. Three design questions decide whether signing adds value: who maintains the allowed-signers list; what happens to commits signed by a key that was later revoked; and whether the host *requires* signed commits or merely displays a badge. A badge without a requirement is decoration. A squash merge performed by the host is signed by the host’s key, not the author’s — so “all commits signed by their authors” is not achievable under mandatory squash, and policy must say which signature matters.

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

### 6. The mutable reference

A release pipeline that resolves a *tag* or *branch name* at deploy time trusts whoever can move that name. Control: protect release tags from update, deploy by immutable commit id or artifact digest, and record the id in the deployment event. A moved tag is a silent substitution; a digest mismatch is a loud one.

### 7. The shadow repository

A team that finds the central rules slow creates a personal-account or unmanaged-organisation repository and deploys from there. No rule on the official repositories can see it. Control: inventory by deployment source, not by host listing — ask “from which repository did this running artifact come?” and flag answers outside the managed set.

## Bypass auditing: from policy to evidence

Bypass is a normal, necessary capability. The control is not its absence but its *visibility and rarity*. Design it as a measurable process.

**Step 1 — inventory who can bypass what.** List every actor with bypass on every ruleset, including administrators, deploy bots and integration apps. Bots are the common blind spot: a token that can push to `main` is a bypass actor even if no human uses it that way.

**Step 2 — make bypass observable.** Export your host’s audit log to a place you control and filter for the event types relating to ruleset bypass, push-protection bypass, rule changes and permission changes. Event names differ by host; learn the schema in your own audit log rather than copying names from another system.

**Step 3 — set a rarity target and alert on breach.** For example: “no more than two direct bypasses per quarter across the organisation; any bypass pages the repository’s owner within five minutes.”

**Step 4 — require an after-the-fact record.** Each bypass links to an incident or change ticket, names the reason, and is reviewed within a fixed window.

An illustrative review query, run weekly against exported audit events (field names are placeholders):

```bash
jq -r 'select(.action | test("bypass|ruleset|protection")) |
       [.created_at, .actor, .repo, .action] | @tsv' audit-export.json \
  | sort | awk -F'\t' '{count[$3]++; print} END {for (r in count) print "TOTAL", r, count[r]}'
```

Interpretation guide:

| Observation | Interpretation | Response |
| --- | --- | --- |
| Zero bypass events for a year | Either excellent discipline or broken logging | Prove logging works with a controlled test bypass |
| Bypass clustered before a quarter-end | Deadline pressure; process too slow | Investigate review latency, not individuals |
| One actor responsible for most events | Informal “release hero” | Rotate; automate the underlying task |
| Bypass by a bot | Automation can ship unreviewed code | Narrow the bot’s scope; require PRs for the bot too |
| Rule disabled then re-enabled | Temporary weakening | Alert on *any* rule change; require ticket link |

**Prove the alarm rings.** Perform a controlled bypass in a disposable repository with the production ruleset pattern, and confirm it appears in the audit export and triggers the alert within the promised time. An unrehearsed alert is an assertion, not a control.

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

### Standards-as-code: a tiered baseline

Not every repository deserves identical controls. Define tiers and attach controls to tiers, so exceptions are *tier changes*, not one-off edits:

| Tier | Typical content | Required controls |
| --- | --- | --- |
| 0 — Critical | Deploy configuration, identity, infrastructure | Two approvals, code-owner review, signed tags, no bypass except named break-glass, workflow-path ownership |
| 1 — Production services | Customer-facing application code | One approval, code-owner review, required checks, push protection, protected release tags |
| 2 — Internal tools | Low-impact services | PR required, required checks, secret scanning |
| 3 — Experiments | Prototypes, spikes | Secret scanning only; auto-archive after N days without activity |

Illustrative provisioning with Terraform (the GitHub provider; verify attribute names for your provider version):

```hcl
variable "repos" {
  type = map(object({ tier = number, owners_team = string }))
}

resource "github_repository_ruleset" "default_branch" {
  for_each    = { for k, v in var.repos : k => v if v.tier <= 1 }
  name        = "protect-default-branch"
  repository  = each.key
  target      = "branch"
  enforcement = "active"

  conditions {
    ref_name {
      include = ["~DEFAULT_BRANCH"]
      exclude = []
    }
  }

  rules {
    deletion         = true
    non_fast_forward = true
    pull_request {
      required_approving_review_count   = each.value.tier == 0 ? 2 : 1
      require_code_owner_review         = true
      dismiss_stale_reviews_on_push     = true
      require_last_push_approval        = true
    }
    required_status_checks {
      strict_required_status_checks_policy = true
      required_check { context = "ci/test" }
      required_check { context = "security/secret-scan" }
    }
  }
}
```

Three properties make this *standards-as-code* rather than scripts: the desired state lives in version control and goes through the same review rules it enforces; changes apply through a pipeline with a plan step; and drift is detected on a schedule rather than discovered during an audit.

### Drift detection

A scheduled job compares actual settings with the declared standard and opens an issue — or fails loudly — on difference:

```bash
#!/usr/bin/env bash
# Illustrative drift check: does every tier-0/1 repository have an active ruleset named protect-default-branch?
set -euo pipefail
ORG="example-org"
status=0
while read -r repo; do
  active=$(gh api "repos/$ORG/$repo/rulesets" --jq '[.[] | select(.name=="protect-default-branch" and .enforcement=="active")] | length')
  if [ "$active" -ne 1 ]; then
    echo "DRIFT: $ORG/$repo has $active active protect-default-branch rulesets"
    status=1
  fi
done < tier01-repos.txt
exit "$status"
```

Drift categories deserve different responses:

| Drift | Cause | Response |
| --- | --- | --- |
| Ruleset missing | New repository created outside the provisioner | Block creation paths; re-apply |
| Ruleset weaker than declared | Manual edit | Re-apply; investigate actor |
| Ruleset stronger than declared | Team over-tightened | Often acceptable — decide whether to adopt it into the standard |
| Repository not in inventory | Shadow repository | Treat as a finding; assign owner or archive |

### Exceptions with expiry

```yaml
# exceptions.yaml — reviewed by platform and security owners
- repo: legacy-billing
  control: require_code_owner_review
  reason: "Owner team dissolved; migration to new team in progress"
  compensating_control: "Weekly manual review by platform lead, evidence in tracker BILL-88"
  approved_by: "security-owner"
  expires: 2027-01-31
```

A scheduled check fails the build when `expires` has passed, forcing a decision: renew with a new reason, or fix the cause. An exception with no expiry is a permanent policy fork with a polite name.

## Traceability end to end

From a running artifact, an expert design can answer:

1. Which commit built it?
2. Who reviewed that commit?
3. Which workflow run produced the artifact?
4. Which approvals gated promotion?

That requires builds to embed commit and run identifiers into artifact metadata, protected refs so those commits remain reachable, and retention of review/run records for as long as the artifact may run. The weak link is rarely Git’s data model; it is human exception handling (“hotfix directly in prod console”) that bypasses the chain.

### Tracing drill

Pick a running artifact in a test environment and perform the trace, recording every hop:

```bash
# 1. From the artifact: read embedded identifiers (label names vary by build system)
docker inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' registry.example/orders-api@sha256:<digest>
# 2. Confirm the commit is reachable from a protected ref
git fetch origin && git branch -r --contains <commit>
# 3. Find the pull request and approvals
git log -1 --format='%H %an %cn %s' <commit>      # then open the associated PR on the host
# 4. Confirm the commit is on the first-parent line of the release branch
git log --first-parent --oneline origin/release/1.4 | grep <short-sha>
```

If any hop fails — no label, commit not on a protected ref, PR deleted, run logs expired — record *which control would have prevented the break*. That list becomes the improvement backlog.

## Large-repository and migration trade-offs

| Pressure | Options | Consequences |
| --- | --- | --- |
| Monorepo clone/CI cost | Sparse checkout, partial clone, remote build caching, split pipelines by path | Contributor tooling complexity |
| Multi-repo version hell | Release trains, automated bump PRs, contract tests | Orchestration burden |
| Split a monorepo | `git filter-repo` into new remotes; freeze old paths | History continuity vs clean breaks; update every consumer |
| Merge many repos | Import with `git subtree` or rewrite; unify ownership | Short-term conflict; long-term ownership redesign |

Migrations fail socially more often than technically: if CODEOWNERS, CI paths and team habits still assume the old layout, the Git rewrite was the easy part.

### Case: sparse checkout and partial clone

A monorepo has grown to 6 GB of history and 400,000 files. A frontend contributor needs only `app/web/` and `docs/`.

```bash
git clone --filter=blob:none --sparse https://git.example/example-org/platform.git
cd platform
git sparse-checkout set --cone app/web docs
git sparse-checkout list
git count-objects -vH
```

What each piece does:

- `--filter=blob:none` is a **partial clone**: commits and trees arrive, file contents (blobs) are fetched lazily on demand.
- `--sparse` starts with only top-level files checked out.
- `sparse-checkout set --cone` limits the working tree to named directories. *Cone* mode is the supported, fast pattern mode; arbitrary patterns are slower and discouraged.

Failure modes to document for contributors:

| Symptom | Cause | Remedy |
| --- | --- | --- |
| `git log -p -- other/dir` is very slow | Missing blobs fetched one at a time | Narrow the history query, or run `git fetch --filter=blob:none origin` selectively; consider a treeless clone for CI |
| A build script reads a path outside the cone and fails | Tool assumes the full tree | Declare required paths in a manifest the sparse setup reads |
| `git grep` seems to miss results | Search is limited to the checked-out cone | Search with `git grep <pattern> origin/main -- <path>` or add directories |
| Offline work fails mid-operation | Promisor remote unreachable | Pre-fetch what is needed; document the dependency on the remote |
| A teammate’s tooling does a shallow clone and `git describe` fails | Missing tags and ancestry | Use `git fetch --tags --unshallow` in CI where version stamping is needed |

CI clones need a different recipe from human clones: `--depth=1` is fastest when only the tip matters, but it breaks tools that compute changed files against `main`, version stamps from tags, and bisection. Choose per job and write the choice into the pipeline, not into tribal knowledge.

### Case: submodules, subtrees and the dependency pin

Your service depends on a shared schema repository. Three ways to include it:

| Option | How it works | Strength | Cost |
| --- | --- | --- | --- |
| Submodule | Parent stores a *commit id* of another repository | Exact pin; separate history and permissions | Extra commands; easy to forget to push or update |
| Subtree / vendoring | Content copied into the parent | Single clone, no extra tooling | History noise; drift from upstream; harder to contribute back |
| Package dependency | Versioned artifact from a registry | Standard tooling; semantic versions | Needs a publishing pipeline |

Submodule mechanics:

```bash
git submodule add https://git.example/example-org/schemas.git vendor/schemas
git commit -m "Add schemas submodule pinned at current tip"
git clone --recurse-submodules https://git.example/example-org/orders-platform.git
git submodule update --init --recursive
git submodule status
```

Illustrative `git submodule status`:

```text
 9f2c4e1a7b3d5f6e8a0b1c2d3e4f5a6b7c8d9e0f vendor/schemas (v2.3.0)
+1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e vendor/schemas (v2.3.0-2-g1d2e3f4)
```

A leading space means the checked-out commit matches the pin; `+` means the submodule is at a *different* commit than the parent records; `-` means not initialised; `U` means merge conflict.

Typical incidents:

| Incident | Cause | Prevention |
| --- | --- | --- |
| Colleague’s clone fails with `upload-pack: not our ref <sha>` | The parent was pushed referencing a submodule commit that was never pushed | `git push --recurse-submodules=check`, or push the submodule first; add a CI check |
| Build uses an older schema than intended | `git pull` does not update the submodule working tree | `git submodule update --init --recursive` in setup scripts; `git config --global submodule.recurse true` |
| Accidental pin bump in an unrelated PR | `git add -A` stages a moved submodule pointer | Review for “Subproject commit” lines; require owner review for the pointer path |
| Detached HEAD inside the submodule confuses contributors | Submodules check out a commit, not a branch | Document: make changes on a branch inside the submodule, push it, then commit the pointer |
| Supply-chain: pin points at an unreviewed upstream commit | No review gate on the pointer update | Treat pointer updates as dependency updates: automated PRs, changelog review |

Choose a submodule when you need an exact, separately-permissioned pin and your contributors tolerate the workflow; choose a package when you have a publishing pipeline; vendor only when upstream is stable and you accept owning drift.

### Narrative 1: splitting a service out of a monorepo

*Situation.* `services/billing/` has an independent team, cadence and compliance scope. The monorepo has 40,000 commits.

*Plan.* Use a **fresh clone** (rewrite tools operate destructively):

```bash
git clone https://git.example/example-org/platform.git billing-extract
cd billing-extract
git filter-repo --path services/billing/ --path-rename services/billing/:
git log --oneline | wc -l          # confirm only billing history remains
git remote add origin https://git.example/example-org/billing.git
git push -u origin main
```

`filter-repo` rewrites every commit id, so *references to old ids* (tickets, release notes, `Fixes <sha>` trailers) become dead. Keep a mapping file (`.git/filter-repo/commit-map`) and publish it.

*Cut-over checklist* — the part that decides success:

1. Freeze `services/billing/` in the monorepo with a CODEOWNERS entry pointing at the migration lead and a CI check that fails any PR touching the path, with a message naming the new repository.
2. Move CI definitions, secrets and environments; rotate any secret that was *shared* with the monorepo pipeline.
3. Re-create ownership, rulesets and required checks in the new repository **before** the first merge, using the tiered standard.
4. Update consumers (build scripts, deploy configuration, documentation links) to the new location.
5. Leave a tombstone `README` in the old path for one release cycle, then remove it.
6. Verify traceability: an artifact built *before* the split still resolves to a commit in the old repository, which must remain readable (archive, not delete).

*What goes wrong.* The first week brings questions about where old review discussions live (still in the monorepo), duplicate bug reports, and a release that deploys from the old path because a pipeline variable still names it. The Git operation took an afternoon; the cut-over took a quarter.

### Narrative 2: consolidating repositories under one standard

*Situation.* Three small repositories (`orders-api`, `orders-worker`, `orders-schemas`) always change together and release in lockstep.

*Approach.* Rewrite each into a subdirectory, then merge the histories:

```bash
for r in orders-api orders-worker orders-schemas; do
  git clone https://git.example/example-org/$r.git tmp-$r
  (cd tmp-$r && git filter-repo --to-subdirectory-filter "services/$r")
done
git init orders-platform && cd orders-platform
for r in orders-api orders-worker orders-schemas; do
  git remote add "$r" "../tmp-$r"
  git fetch "$r"
  git merge --allow-unrelated-histories "$r/main" -m "Import $r history"
done
```

`--allow-unrelated-histories` is correct *here* because the histories genuinely are unrelated; it is the explicit, reviewed form of the flag Beginner readers are warned about. Afterwards, unify CODEOWNERS, merge CI definitions with path filters, and archive the old repositories read-only with a pointer. Open issues and pull requests do not migrate with Git; plan their transfer separately.

### Narrative 3: renaming the default branch and moving hosts

A default-branch rename is cheap in Git and expensive in *references*:

```bash
git branch -m master main
git push -u origin main
# On the host: change the default branch, update rulesets and required checks that name the branch
git push origin --delete master      # only after every consumer has moved
# Every contributor, once:
git fetch origin && git branch -u origin/main main && git remote set-head origin -a
```

Search for the old name in CI, deployment scripts, badge URLs, documentation, protection rules, webhook filters and scheduled jobs. Run a **dual-name period** (keep a protected `master` that fast-forwards from `main`, or redirect) with a written end date.

A host migration adds mirror-and-verify steps:

```bash
git clone --mirror https://old.example/example-org/orders-platform.git
cd orders-platform.git
git push --mirror https://new.example/example-org/orders-platform.git
# Verify equality of refs, not just "it pushed"
git ls-remote https://old.example/example-org/orders-platform.git | sort > old.txt
git ls-remote https://new.example/example-org/orders-platform.git | sort > new.txt
diff old.txt new.txt
```

A mirror carries Git data only: rulesets, secrets, webhooks, deploy keys, issues, review history and LFS objects need separate migration, and a **secret store migration is a rotation opportunity** — do not copy credentials you can reissue.

### Narrative 4: a formatting-only mass change without ruining blame

Reformatting 3,000 files in one commit makes `git blame` useless: every line now “belongs” to the formatter. Preserve usefulness:

```bash
git commit -m "style: apply formatter to entire repository"
git rev-parse HEAD >> .git-blame-ignore-revs
git config blame.ignoreRevsFile .git-blame-ignore-revs
git blame --ignore-revs-file .git-blame-ignore-revs app/handler.py
```

Commit `.git-blame-ignore-revs`, tell the team to set the config once, and land the formatting commit **alone** (never mixed with behaviour). Many hosts honour the file in their blame view automatically.

### Narrative 5: a rewrite after a leak — decide, then execute

*Situation.* A cloud key was committed to `main`, noticed six hours later, rotated at once. The commit also contained a customer export file.

*Decision.* The key is dead after rotation, so rewriting would not help for the key. The customer data is not rotatable, so removal from history is justified — a regulatory and contractual decision, not a Git preference.

*Execution outline:*

```bash
git clone --mirror https://git.example/example-org/orders-platform.git
cd orders-platform.git
git filter-repo --analyze                       # confirm what is large or sensitive
git filter-repo --invert-paths --path exports/customers.csv
git push --force --mirror origin                # only inside an announced, host-permitted window
```

Then: ask the host to purge cached views and pull-request refs that still reference the old commits (a force-push does not remove them from the host’s object store on every platform); notify all contributors to re-clone rather than merge; sweep forks, mirrors, CI caches and artifacts; and record exactly what could not be recalled. Rewriting reduces *future* exposure; it does not undo *past* copies.

## Adversarial and contested questions

Use these as design reviews, not trivia:

- Why can `git reset --hard` followed by force-push be legitimate on a private branch and a policy violation on the default branch in the same hour?
- What evidence would convince you CODEOWNERS is enforced for administrators, not only for ordinary contributors?
- Which of your controls still hold if a maintainer’s account is phished?
- If squash merges are mandatory, how do you bisect production regressions that landed inside a 2,000-line squash?
- When is a submodule preferable to vendoring or a monorepo package — and what operational pain are you accepting?

### Worked answers to the contested questions

**Reset-and-force-push, two refs.** On a private branch, history rewriting affects only the owner, so recoverability is the owner’s concern. On the default branch, the rewrite invalidates everyone’s clones, breaks the linkage between artifacts and commit ids, and erases audit evidence. The *same commands* differ in *blast radius*, which is why the control is a ruleset on the shared ref, not training alone.

**Administrator enforcement.** Convincing evidence is a recorded attempt: an admin account opens a PR touching an owned path and cannot merge without owner approval, *and* the ruleset’s bypass list does not include administrators (or includes them in pull-request-only mode, with the resulting audit event). A settings screenshot proves intent only.

**Phished maintainer.** Controls that still hold: second reviewer on sensitive paths, required checks defined outside the maintainer’s control, short-lived deploy credentials issued per run, tag protection, and alerting on unusual bypass or rule edits. Controls that fail: any single-approver rule where the attacker also controls the author account, and any token the maintainer can mint with broad scope.

**Bisecting a large squash.** Keep the original branch commits reachable for a retention window (the host’s PR page often preserves them), cap PR size so squashes stay small, or require merge commits for large changes. Without one of these, localisation depends on reading a monolithic diff.

**Submodule versus alternatives.** Choose the submodule for an exact pin with separate permissions; accept the extra clone/update steps, pointer-bump review, and contributor confusion. If you have no appetite for documenting those, publish a package.

## Knowledge consolidation

- Scale turns local Git craft into **organisational control design**.
- Every powerful tool (`rerere`, rewrite, bypass, signatures) has a failure mode; name it in the design.
- Traceability is a chain; exceptions break the chain even when Git is healthy.
- Standards-as-code plus expiring exceptions beat wiki aspiration.
- Expert judgement is knowing when **not** to rewrite, rebase or centralise.
- Git remembers that a change was *merged*, not only that it is *present*; revert-of-revert is the ledger-aware repair.
- Bypass is a capability to be **audited and rehearsed**, not a vice to be denied.
- Migrations are mostly about references — tickets, pipelines, ownership, habits — not about the Git operation.
- Partial clones, sparse checkout and submodules trade disk and time for workflow complexity; document the recipe per audience.

## Exercises

**Exercise 1.** Draft a one-page “repository standard” for 80 application repositories: mandatory controls, allowed team choices, exception process with expiry, and how drift is detected.

**Exercise 2.** Given a merge commit that brought a bad feature onto `main`, write the exact revert command sequence, then explain how you would re-introduce a fixed version of the feature without resurrecting the bug via a naive merge.

**Exercise 3 (challenge).** A secret was pushed to `main`, mirrored to a backup host, and built into a container registry layer. Outline the incident response across credential rotation, registry, mirrors and communication — and state which steps Git history rewrite cannot accomplish alone.

**Exercise 4 — Tiers and drift.** Define four tiers for your own organisation (use the table above as a starting point), assign ten fictional repositories, and write the drift query that would detect a tier-1 repository without a required status check. State what a *false negative* from that query would look like.

**Exercise 5 — Bypass design.** Write the bypass policy for a team of 12: who holds it, what events alert, the rarity target, the after-the-fact record and the rehearsal. Describe the controlled test you would run each quarter and what result would count as failure.

**Exercise 6 — Sparse recipe.** For a monorepo with `app/web`, `app/api`, `infra` and `docs`, write three clone recipes — a frontend contributor, a platform engineer and a CI job that stamps versions from tags — and list one thing that breaks under each recipe if the recipe is misapplied.

**Exercise 7 — Submodule incident.** A teammate reports `not our ref` when cloning with submodules. Write the diagnosis steps, the fix, and the CI check that would have prevented it.

**Exercise 8 — Migration plan.** Plan the extraction of one service from a monorepo using the cut-over checklist. Add a rollback plan that works *after* the first merge in the new repository.

**Solution notes.** Exercise 2 should use `git revert -m 1` after confirming parents; re-introduction usually needs revert-of-revert or reimplemented commits. Exercise 3 must treat registry and mirrors as first-class exposure surfaces; rewrite without rotation is theatre.

**Solution notes (Exercise 4).** A false negative would be a repository where the check name exists but is path-filtered or optional, so the query sees a ruleset yet the gate does not actually fire. Mitigate by periodically opening a test PR rather than relying on settings alone.

**Solution notes (Exercise 5).** Failure is any outcome where a controlled bypass does not appear in the audit export or does not trigger the alert inside the promised window.

**Solution notes (Exercise 6).** Typical breakages: the frontend recipe cannot build because the build reads `infra/` for a version file; the CI shallow clone cannot run `git describe`; the platform recipe pulls far more than needed if the cone was not applied.

**Solution notes (Exercise 7).** The parent commit references a submodule commit that was never pushed. Push the submodule commit, then add a CI job running `git submodule update --init --recursive` on every pull request so the failure appears before merge.

**Solution notes (Exercise 8).** A workable rollback keeps the monorepo path frozen but intact for the duration of the migration window and keeps a documented way to re-import post-split commits back as a patch series.
